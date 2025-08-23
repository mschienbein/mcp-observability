import './ModelSelector.css';

const AVAILABLE_MODELS = [
  { id: 'anthropic.claude-3-haiku-20240307-v1:0', name: 'Claude 3 Haiku (Fast)' },
  { id: 'anthropic.claude-3-sonnet-20240229-v1:0', name: 'Claude 3 Sonnet' },
  { id: 'anthropic.claude-3-5-sonnet-20241022-v2:0', name: 'Claude 3.5 Sonnet' },
  { id: 'anthropic.claude-3-opus-20240229-v1:0', name: 'Claude 3 Opus' },
  { id: 'meta.llama3-1-70b-instruct-v1:0', name: 'Llama 3.1 70B' },
  { id: 'amazon.nova-pro-v1:0', name: 'Amazon Nova Pro' },
];

function ModelSelector({ selectedModel, onModelChange }) {
  return (
    <div className="model-selector">
      <label htmlFor="model-select">Model:</label>
      <select
        id="model-select"
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value)}
        className="model-select"
      >
        {AVAILABLE_MODELS.map(model => (
          <option key={model.id} value={model.id}>
            {model.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export default ModelSelector;