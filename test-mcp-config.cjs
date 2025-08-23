#!/usr/bin/env node

/**
 * Test script to verify MCP configuration in LibreChat
 */

const fs = require('fs');
const yaml = require('js-yaml');
const path = require('path');

console.log('🔍 Checking MCP Configuration for LibreChat...\n');

// Check librechat.yaml
const yamlPath = path.join(__dirname, 'librechat-source', 'librechat.yaml');
if (!fs.existsSync(yamlPath)) {
    console.error('❌ librechat.yaml not found at:', yamlPath);
    process.exit(1);
}

const config = yaml.load(fs.readFileSync(yamlPath, 'utf8'));

// Check MCP servers
if (!config.mcpServers) {
    console.error('❌ No mcpServers configuration found');
    process.exit(1);
}

console.log('✅ MCP Servers Configured:');
console.log('===========================\n');

for (const [name, serverConfig] of Object.entries(config.mcpServers)) {
    console.log(`📦 ${name}`);
    console.log(`   Command: ${serverConfig.command} ${serverConfig.args?.join(' ') || ''}`);
    console.log(`   Startup: ${serverConfig.startup ?? 'not set (defaults to true)'}`);
    console.log(`   Chat Menu: ${serverConfig.chatMenu ?? 'not set (defaults to false)'} ${!serverConfig.chatMenu ? '⚠️  NEEDS chatMenu: true to appear in UI!' : '✅'}`);
    console.log(`   Description: ${serverConfig.description || 'None'}`);
    console.log('');
}

// Check .env file
const envPath = path.join(__dirname, 'librechat-source', '.env');
if (!fs.existsSync(envPath)) {
    console.error('⚠️  .env file not found');
} else {
    const envContent = fs.readFileSync(envPath, 'utf8');
    const mcpEnabled = envContent.includes('MCP_ENABLED=true');
    const enableMcp = envContent.includes('ENABLE_MCP=true');
    
    console.log('Environment Variables:');
    console.log('======================');
    console.log(`MCP_ENABLED: ${mcpEnabled ? '✅ true' : '❌ not found or false'}`);
    console.log(`ENABLE_MCP: ${enableMcp ? '✅ true' : '❌ not found or false'}`);
    console.log('');
}

// Summary
console.log('\n📋 Summary:');
console.log('===========');
const mcpUiTools = config.mcpServers['mcp-ui-tools'];
if (mcpUiTools) {
    if (mcpUiTools.chatMenu === true && (mcpUiTools.startup === true || mcpUiTools.startup === undefined)) {
        console.log('✅ MCP UI Tools server is properly configured!');
        console.log('   It should appear in the LibreChat UI when you run the app.');
    } else {
        console.log('⚠️  MCP UI Tools server needs adjustment:');
        if (!mcpUiTools.chatMenu) {
            console.log('   - Add: chatMenu: true');
        }
        if (mcpUiTools.startup === false) {
            console.log('   - Change startup to: true (or remove it)');
        }
    }
} else {
    console.log('❌ MCP UI Tools server not found in configuration');
}

console.log('\n🚀 To start LibreChat with MCP:');
console.log('   ./start-librechat-mcp.sh');