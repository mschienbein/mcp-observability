import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { streamText } from 'ai';
import { bedrock } from '@ai-sdk/amazon-bedrock';

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// Chat endpoint
app.post('/api/chat', async (req, res) => {
  try {
    const { messages, model, tools } = req.body;

    // Configure Bedrock
    const bedrockModel = bedrock(model || 'anthropic.claude-3-haiku-20240307-v1:0', {
      region: process.env.VITE_AWS_REGION || 'us-east-1',
      accessKeyId: process.env.VITE_AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.VITE_AWS_SECRET_ACCESS_KEY,
    });

    // Stream the response
    const result = await streamText({
      model: bedrockModel,
      messages: messages,
      system: 'You are a helpful AI assistant with access to various tools through MCP.',
      maxTokens: 4096,
      temperature: 0.7,
    });

    // Set headers for streaming
    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
    res.setHeader('Transfer-Encoding', 'chunked');

    // Stream the response
    for await (const textPart of result.textStream) {
      res.write(textPart);
    }

    res.end();
  } catch (error) {
    console.error('Chat API error:', error);
    res.status(500).json({ 
      error: 'An error occurred',
      details: error.message 
    });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`API server running on http://localhost:${PORT}`);
});