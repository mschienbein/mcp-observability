import React, { useEffect, useRef, useState } from 'react';
import { UIResourceRenderer } from '@mcp-ui/client';
import type { MCPResource } from '~/Providers/MCPResourceContext';
import type { UIActionResult } from '@mcp-ui/client/dist/src/types';

export interface MCPUIResourceRendererProps {
  resource: MCPResource;
  onUIAction?: (result: UIActionResult) => void | Promise<unknown>;
  className?: string;
  style?: React.CSSProperties;
}

export function MCPUIResourceRenderer({
  resource,
  onUIAction,
  className,
  style,
}: MCPUIResourceRendererProps) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const directIframeRef = useRef<HTMLIFrameElement | null>(null);
  const [iframeHeight, setIframeHeight] = useState<number>(150); // Start with minimal height
  const [isLoaded, setIsLoaded] = useState(false);
  const iframeLoadedRef = useRef(false);
  const trackedIframesRef = useRef<HTMLIFrameElement[]>([]);
  const rafRef = useRef<number | null>(null);
  const pendingHeightRef = useRef<number | null>(null);
  const iframeObserversRef = useRef<Map<HTMLIFrameElement, ResizeObserver>>(new Map());
  const applyHeight = (h: number) => {
    const next = Math.max(0, Math.ceil(h));
    setIframeHeight((prev) => (next > prev ? next : prev));
  };
  const scheduleHeightCommit = (h: number) => {
    pendingHeightRef.current = Math.max(pendingHeightRef.current ?? 0, h);
    if (rafRef.current != null) return;
    rafRef.current = requestAnimationFrame(() => {
      const ph = pendingHeightRef.current;
      rafRef.current = null;
      pendingHeightRef.current = null;
      if (typeof ph === 'number') {
        applyHeight(ph);
        setIsLoaded(true);
      }
    });
  };

  const attachIframeObservers = () => {
    const map = iframeObserversRef.current;
    const set = new Set(trackedIframesRef.current);
    // Remove observers for iframes no longer present
    for (const [iframe, ro] of map.entries()) {
      if (!set.has(iframe)) {
        try { ro.disconnect(); } catch {}
        map.delete(iframe);
      }
    }
    // Add observers for new iframes
    trackedIframesRef.current.forEach((iframe) => {
      if (map.has(iframe)) return;
      const ro = new ResizeObserver((entries) => {
        for (const e of entries) {
          const h = Math.max(
            e.contentRect?.height || 0,
            (iframe.clientHeight || 0),
            (iframe.offsetHeight || 0),
          );
          if (h) {
            console.log('[MCPUIRenderer] ResizeObserver iframe height:', h);
            scheduleHeightCommit(h);
          }
        }
      });
      try { ro.observe(iframe); } catch {}
      map.set(iframe, ro);
    });
  };

  const settleProbe = (frames = 6, delayMs = 0) => {
    const run = (n: number) => {
      if (n <= 0) return;
      const measure = () => {
        const ifr = trackedIframesRef.current[0];
        if (ifr) {
          let h = Math.max(ifr.clientHeight || 0, ifr.offsetHeight || 0);
          try {
            const doc = ifr.contentDocument || ifr.contentWindow?.document;
            if (doc) {
              const body = doc.body as HTMLElement | null;
              const html = doc.documentElement as HTMLElement | null;
              const rectH = body?.getBoundingClientRect?.().height || 0;
              const bodyH = Math.max(body?.scrollHeight || 0, body?.offsetHeight || 0, body?.clientHeight || 0);
              const htmlH = Math.max(html?.scrollHeight || 0, html?.offsetHeight || 0, html?.clientHeight || 0);
              h = Math.max(h, rectH, bodyH, htmlH);
            }
          } catch {}
          if (h) scheduleHeightCommit(h);
        }
        requestAnimationFrame(() => run(n - 1));
      };
      if (delayMs > 0) setTimeout(measure, delayMs); else measure();
    };
    run(frames);
  };

  // Apply computed height directly on tracked iframe elements to avoid inner scrollbars
  useEffect(() => {
    const px = `${iframeHeight}px`;
    trackedIframesRef.current.forEach((ifr) => {
      try {
        ifr.style.height = px;
        ifr.style.minHeight = px;
        ifr.style.maxHeight = 'none';
        ifr.setAttribute('scrolling', 'no');
        (ifr.style as any).overflow = 'hidden';
      } catch {}
    });
  }, [iframeHeight]);
  
  console.log('[MCPUIRenderer] Component rendered, resource:', resource?.uri, 'current height:', iframeHeight);
  
  useEffect(() => {
    console.log('[MCPUIRenderer] useEffect running, wrapperRef:', !!wrapperRef.current);
    if (!wrapperRef.current) return;
    
    // Function to handle messages from iframe
    const handleMessage = (event: MessageEvent) => {
      console.log('[MCPUIRenderer] Received message:', event.data);
      // Only accept messages from iframes we own, BUT allow early events before tracking attaches
      try {
        const iframes = trackedIframesRef.current;
        const fromIframe = iframes.some((f) => f.contentWindow === (event.source as Window | null));
        if (!fromIframe && iframes.length > 0) return;
      } catch {}
      // Height update messages (support several shapes)
      const type = event.data?.type;
      if (type === 'mcp-ui-height-update' || type === 'ui-size-change' || type === 'mcp-ui:size') {
        const payload = event.data?.payload ?? event.data;
        const newHeight =
          payload?.height ??
          payload?.size?.height ??
          payload?.innerHeight ??
          payload?.contentHeight;
        console.log('[MCPUIRenderer] Height update message, newHeight:', newHeight);
        if (typeof newHeight === 'number' && isFinite(newHeight)) {
          scheduleHeightCommit(newHeight);
        }
      }
    };

    const refreshTrackedIframes = () => {
      if (!wrapperRef.current) return;
      const list = Array.from(wrapperRef.current.querySelectorAll('iframe')) as HTMLIFrameElement[];
      if (directIframeRef.current && !list.includes(directIframeRef.current)) {
        list.unshift(directIframeRef.current);
      }
      trackedIframesRef.current = list;
      attachIframeObservers();
    };
    
    // Listen for messages from iframe
    window.addEventListener('message', handleMessage);
    console.log('[MCPUIRenderer] Message listener attached');
    
    // Function to inject height detection script into iframe
    const injectHeightDetector = (iframe: HTMLIFrameElement) => {
      console.log('[MCPUIRenderer] injectHeightDetector called, iframe:', !!iframe);
      if (!iframe) return;
      
      const attemptInjection = () => {
        console.log('[MCPUIRenderer] Attempting script injection...');
        try {
          const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
          console.log('[MCPUIRenderer] Iframe document accessible:', !!iframeDoc);
          if (!iframeDoc) {
            console.warn('[MCPUIRenderer] No iframe document available');
            return;
          }
          
          // Check if script already injected
          if (iframeDoc.querySelector('[data-mcp-height-detector]')) {
            console.log('[MCPUIRenderer] Script already injected, skipping');
            return;
          }
          
          // Inject script to measure and report height
          const script = iframeDoc.createElement('script');
          script.setAttribute('data-mcp-height-detector', 'true');
          script.textContent = `
            (function() {
              console.log('[IframeScript] Height detector script starting...');
              
              function getDocumentHeight() {
                const body = document.body;
                const html = document.documentElement;
                
                // Get various height measurements
                const heights = [
                  body.scrollHeight,
                  body.offsetHeight,
                  body.clientHeight,
                  html.scrollHeight,
                  html.offsetHeight,
                  html.clientHeight
                ];
                
                // Also check for absolutely positioned elements
                const allElements = document.querySelectorAll('*');
                let maxBottom = 0;
                allElements.forEach(el => {
                  const rect = el.getBoundingClientRect();
                  const style = window.getComputedStyle(el);
                  const marginBottom = parseInt(style.marginBottom) || 0;
                  const bottom = rect.bottom + marginBottom;
                  if (bottom > maxBottom) maxBottom = bottom;
                });
                
                heights.push(maxBottom);
                
                // Return the maximum height
                const maxHeight = Math.max(...heights.filter(h => !isNaN(h)));
                console.log('[IframeScript] Computed height:', maxHeight, 'from heights:', heights);
                return maxHeight;
              }
              
              function sendHeight() {
                const height = getDocumentHeight();
                console.log('[IframeScript] Sending height to parent:', height);
                // Send to parent window
                if (window.parent !== window) {
                  window.parent.postMessage({
                    type: 'mcp-ui-height-update',
                    height: height
                  }, '*');
                }
              }
              
              // Send initial height after a short delay
              console.log('[IframeScript] Scheduling initial height send...');
              setTimeout(sendHeight, 100);
              setTimeout(sendHeight, 500);
              setTimeout(sendHeight, 1000);
              
              // Set up ResizeObserver to detect content changes
              if (window.ResizeObserver) {
                console.log('[IframeScript] Setting up ResizeObserver...');
                const resizeObserver = new ResizeObserver(() => {
                  console.log('[IframeScript] ResizeObserver triggered');
                  sendHeight();
                });
                resizeObserver.observe(document.body);
                resizeObserver.observe(document.documentElement);
              }
              
              // Also observe DOM mutations
              console.log('[IframeScript] Setting up MutationObserver...');
              const mutationObserver = new MutationObserver(() => {
                console.log('[IframeScript] MutationObserver triggered');
                sendHeight();
              });
              mutationObserver.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                characterData: true
              });
              
              // Listen for window resize
              window.addEventListener('resize', sendHeight);
              
              // Listen for images loading
              document.querySelectorAll('img').forEach(img => {
                if (!img.complete) {
                  img.addEventListener('load', sendHeight);
                }
              });
              
              // Periodic check as fallback
              setInterval(() => {
                console.log('[IframeScript] Periodic height check');
                sendHeight();
              }, 2000);
            })();
          `;
          iframeDoc.head?.appendChild(script);
          console.log('[MCPUIRenderer] Script injected successfully');
          setIsLoaded(true);
          iframeLoadedRef.current = true;
        } catch (e) {
          console.warn('[MCPUIRenderer] Could not inject height detector (cross-origin?):', e);
          // Fall back to resource-specified height or default
          const fallbackHeight = 
            resource?.height || 
            resource?.metadata?.height || 
            600;
          console.log('[MCPUIRenderer] Using fallback height:', fallbackHeight);
          setIframeHeight(fallbackHeight);
        }
      };
      
      // Try injection immediately if iframe is already loaded
      if (iframe.contentDocument?.readyState === 'complete') {
        console.log('[MCPUIRenderer] Iframe already complete, injecting now');
        attemptInjection();
      }
      
      // Also listen for load event
      const loadHandler = () => {
        console.log('[MCPUIRenderer] Iframe load event fired');
        attemptInjection();
        refreshTrackedIframes();
      };
      
      iframe.addEventListener('load', loadHandler);
      
      // Cleanup
      return () => {
        iframe.removeEventListener('load', loadHandler);
      };
    };
    
    // Set up observer to detect when iframe is added
    const observer = new MutationObserver((mutations) => {
      console.log('[MCPUIRenderer] MutationObserver triggered, checking for iframes...');
      
      for (const mutation of mutations) {
        // Check added nodes for iframes
        for (const node of Array.from(mutation.addedNodes)) {
          if (node instanceof HTMLIFrameElement) {
            console.log('[MCPUIRenderer] Found iframe in added nodes');
            injectHeightDetector(node);
          }
          // Also check children of added nodes
          if (node instanceof HTMLElement) {
            const iframes = node.querySelectorAll('iframe');
            iframes.forEach((iframe) => {
              console.log('[MCPUIRenderer] Found iframe in child nodes');
              injectHeightDetector(iframe as HTMLIFrameElement);
            });
          }
        }
      }
      refreshTrackedIframes();
    });
    
    observer.observe(wrapperRef.current, {
      childList: true,
      subtree: true
    });
    console.log('[MCPUIRenderer] MutationObserver set up');
    refreshTrackedIframes();
    
    // Try to find and inject into existing iframes
    const existingIframes = wrapperRef.current.querySelectorAll('iframe');
    console.log('[MCPUIRenderer] Found existing iframes:', existingIframes.length);
    existingIframes.forEach((iframe) => {
      injectHeightDetector(iframe as HTMLIFrameElement);
    });
    refreshTrackedIframes();
    settleProbe(8, 0);
    
    // Also check after a short delay in case the iframe is rendered async
    setTimeout(() => {
      const delayedIframes = wrapperRef.current?.querySelectorAll('iframe');
      console.log('[MCPUIRenderer] Delayed check found iframes:', delayedIframes?.length || 0);
      delayedIframes?.forEach((iframe) => {
        injectHeightDetector(iframe as HTMLIFrameElement);
      });
      refreshTrackedIframes();
      settleProbe(6, 50);
    }, 500);
    
    return () => {
      console.log('[MCPUIRenderer] Cleaning up...');
      window.removeEventListener('message', handleMessage);
      observer.disconnect();
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      pendingHeightRef.current = null;
      for (const ro of iframeObserversRef.current.values()) { try { ro.disconnect(); } catch {} }
      iframeObserversRef.current.clear();
    };
  }, [resource]);
  
  return (
    <div
      ref={wrapperRef}
      className={['w-full max-w-full overflow-visible', className].filter(Boolean).join(' ')}
      style={{ 
        width: '100%',
        overflow: 'visible',
        minHeight: `${iframeHeight}px`,
        height: 'auto',
        maxHeight: 'none',
        display: 'block',
        transition: 'min-height 0.2s ease',
        ...style
      }}
    >
      <UIResourceRenderer
        resource={resource}
        htmlProps={{
          autoResizeIframe: true, // Let library emit size changes and adjust iframe
          sandboxPermissions: 'allow-scripts allow-same-origin',
          iframeProps: {
            ref: directIframeRef,
          },
          style: {
            width: '100%',
            display: 'block',
            border: 'none',
            overflow: 'hidden',
            maxHeight: 'none',
          }
        }}
        onUIAction={async (result) => {
          if (onUIAction) {
            await Promise.resolve(onUIAction(result));
          }
        }}
      />
    </div>
  );
}

export default MCPUIResourceRenderer;
