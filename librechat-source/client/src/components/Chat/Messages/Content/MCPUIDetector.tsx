import type { MCPResource } from '~/Providers/MCPResourceContext';

/**
 * Detects if a tool output contains an MCP UI resource
 */
export function detectMCPUIResource(output: string | null | undefined): {
  isMCPResource: boolean;
  resource?: MCPResource;
} {
  if (!output) {
    console.log('detectMCPUIResource: No output provided');
    return { isMCPResource: false };
  }

  try {
    // Helper to check if an object is a valid MCP UI resource wrapper
    const tryExtractResource = (obj: any): MCPResource | undefined => {
      if (!obj) return undefined;
      const candidate = obj?.type === 'resource' ? obj : undefined;
      const resource = candidate?.resource ?? undefined;
      if (
        resource?.uri?.startsWith?.('ui://') &&
        (resource?.mimeType === 'text/html' || resource?.mimeType === 'text/xhtml') &&
        (typeof resource?.text === 'string' && resource.text.length > 0)
      ) {
        return resource as MCPResource;
      }
      return undefined;
    };

    // Parse the output as JSON (may be an object or an array string)
    const parsed = JSON.parse(output);

    const logParsedShape = (value: any, label: string) => {
      if (Array.isArray(value)) {
        console.log(`detectMCPUIResource: Parsed JSON (${label}) is array`, {
          length: value.length,
          firstItemType: value[0]?.type,
        });
      } else if (typeof value === 'object' && value !== null) {
        console.log(`detectMCPUIResource: Parsed JSON (${label}) is object`, {
          type: value?.type,
          hasResource: !!value?.resource,
          uri: value?.resource?.uri,
          mimeType: value?.resource?.mimeType,
          hasText: !!value?.resource?.text,
          textLength: value?.resource?.text?.length,
        });
      } else {
        console.log(`detectMCPUIResource: Parsed JSON (${label}) is primitive`, typeof value);
      }
    };

    logParsedShape(parsed, 'top-level');

    // 1) Direct resource object
    const direct = tryExtractResource(parsed);
    if (direct) {
      console.log('detectMCPUIResource: ✅ MCP UI Resource detected (direct)!', direct.uri);
      return { isMCPResource: true, resource: direct };
    }

    // 2) Wrapper with { type: 'text', text: '{"type":"resource", ... }' }
    if (parsed && typeof parsed === 'object' && parsed.type === 'text' && typeof parsed.text === 'string') {
      try {
        const inner = JSON.parse(parsed.text);
        logParsedShape(inner, 'inner-from-text');
        const extracted = tryExtractResource(inner);
        if (extracted) {
          console.log('detectMCPUIResource: ✅ MCP UI Resource detected (text->inner)!', extracted.uri);
          return { isMCPResource: true, resource: extracted };
        }
      } catch (e) {
        console.log('detectMCPUIResource: Failed to parse inner text JSON', e);
      }
    }

    // 3) Array of items (e.g., [{ type: 'text', text: '...json...' }])
    if (Array.isArray(parsed)) {
      for (const item of parsed) {
        // 3a) Each item might directly be a resource wrapper
        const fromItem = tryExtractResource(item);
        if (fromItem) {
          console.log('detectMCPUIResource: ✅ MCP UI Resource detected (array item direct)!', fromItem.uri);
          return { isMCPResource: true, resource: fromItem };
        }
        // 3b) Or a text wrapper with JSON string inside
        if (item?.type === 'text' && typeof item?.text === 'string') {
          try {
            const inner = JSON.parse(item.text);
            logParsedShape(inner, 'array-item-inner-from-text');
            const extracted = tryExtractResource(inner);
            if (extracted) {
              console.log('detectMCPUIResource: ✅ MCP UI Resource detected (array item text->inner)!', extracted.uri);
              return { isMCPResource: true, resource: extracted };
            }
          } catch (e) {
            // Continue scanning other items
            console.log('detectMCPUIResource: Failed to parse array item inner text JSON', e);
          }
        }
      }
    }
  } catch (e) {
    console.log('detectMCPUIResource: Failed to parse as JSON', e);
  }

  return { isMCPResource: false };
}