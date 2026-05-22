#!/usr/bin/env node

'use strict';

const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
let mainPath = '';
let preloadPath = '';
let contractPath = '';
let verbose = false;

function parseArgs() {
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--main':
        mainPath = args[++i];
        break;
      case '--preload':
        preloadPath = args[++i];
        break;
      case '--contract':
        contractPath = args[++i];
        break;
      case '--verbose':
        verbose = true;
        break;
      case '--help':
        printHelp();
        process.exit(0);
      default:
        console.error(`Unknown argument: ${args[i]}`);
        process.exit(1);
    }
  }
}

function printHelp() {
  console.log(`
IPC Contract Validator

Validates IPC channel definitions match between main process, preload, and contract docs.

Usage:
  node ipc-contract-validator.js --main ./main.js --preload ./preload.js --contract ./ipc-contracts.md

Options:
  --main      Path to main process file
  --preload   Path to preload script file
  --contract  Path to IPC contract markdown file
  --verbose   Show detailed output
  --help      Show this help message
`);
}

function extractIpcMainChannels(source) {
  const channels = new Set();
  const handleRegex = /ipcMain\.handle\(\s*['"`]([^'"`]+)['"`]/g;
  const onRegex = /ipcMain\.on\(\s*['"`]([^'"`]+)'['"`]/g;

  let match;
  while ((match = handleRegex.exec(source)) !== null) {
    channels.add({ name: match[1], type: 'handle' });
  }
  while ((match = onRegex.exec(source)) !== null) {
    channels.add({ name: match[1], type: 'on' });
  }
  return [...channels];
}

function extractIpcRendererChannels(source) {
  const channels = new Set();
  const invokeRegex = /ipcRenderer\.invoke\(\s*['"`]([^'"`]+)['"`]/g;
  const sendRegex = /ipcRenderer\.send\(\s*['"`]([^'"`]+)'['"`]/g;
  const onRegex = /ipcRenderer\.on\(\s*['"`]([^'"`]+)'['"`]/g;
  const sendSyncRegex = /ipcRenderer\.sendSync\(\s*['"`]([^'"`]+)'['"`]/g;

  let match;
  while ((match = invokeRegex.exec(source)) !== null) {
    channels.add({ name: match[1], type: 'invoke' });
  }
  while ((match = sendRegex.exec(source)) !== null) {
    channels.add({ name: match[1], type: 'send' });
  }
  while ((match = onRegex.exec(source)) !== null) {
    channels.add({ name: match[1], type: 'on' });
  }
  while ((match = sendSyncRegex.exec(source)) !== null) {
    channels.add({ name: match[1], type: 'sendSync' });
  }
  return [...channels];
}

function extractPreloadExposedChannels(source) {
  const channels = new Set();
  const exposeRegex = /contextBridge\.exposeInMainWorld\(\s*['"`]([^'"`]+)['"`]\s*,\s*\{([^}]+)\}/g;

  let match;
  while ((match = exposeRegex.exec(source)) !== null) {
    const objectBody = match[2];
    const methodRegex = /(\w+)\s*:\s*\([^)]*\)\s*=>\s*ipcRenderer\.(invoke|send|sendSync|on)\s*\(\s*['"`]([^'"`]+)'['"`]/g;
    let methodMatch;
    while ((methodMatch = methodRegex.exec(objectBody)) !== null) {
      channels.add({
        apiName: match[1],
        methodName: methodMatch[1],
        channelName: methodMatch[3],
        type: methodMatch[2]
      });
    }
  }
  return [...channels];
}

function extractContractChannels(markdown) {
  const channels = new Set();
  const channelRegex = /\|\s*Channel Name\s*\|\s*`([^`]+)`\s*\|/g;
  const headingRegex = /^##\s+.*`([^`]+)`/gm;
  const codeBlockRegex = /ipcMain\.handle\(\s*['"`]([^'"`]+)'['"`]/g;
  const invokeRegex = /ipcRenderer\.invoke\(\s*['"`]([^'"`]+)'['"`]/g;
  const tauriCommandRegex = /#\[(?:command|tauri::command)\][\s\S]*?pub\s+async\s+fn\s+(\w+)/g;

  let match;
  while ((match = channelRegex.exec(markdown)) !== null) {
    channels.add(match[1]);
  }
  while ((match = headingRegex.exec(markdown)) !== null) {
    channels.add(match[1]);
  }
  while ((match = codeBlockRegex.exec(markdown)) !== null) {
    channels.add(match[1]);
  }
  while ((match = invokeRegex.exec(markdown)) !== null) {
    channels.add(match[1]);
  }
  while ((match = tauriCommandRegex.exec(markdown)) !== null) {
    channels.add(match[1].replace(/_/g, ':'));
  }
  return [...channels];
}

function checkErrorHandlers(source, channelName) {
  const channelBlockRegex = new RegExp(
    `ipcMain\\.handle\\(\\s*['"\`]${escapeRegex(channelName)}['"\`]\\s*,[\\s\\S]*?(?=ipcMain\\.|$)`,
    'g'
  );
  const block = channelBlockRegex.exec(source);
  if (!block) return false;
  return block[0].includes('try') && block[0].includes('catch');
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function validate() {
  parseArgs();

  const errors = [];
  const warnings = [];
  const info = [];

  if (!mainPath && !preloadPath && !contractPath) {
    console.error('Error: At least one of --main, --preload, or --contract is required.');
    process.exit(1);
  }

  let mainChannels = [];
  let preloadChannels = [];
  let contractChannels = [];

  if (mainPath) {
    if (!fs.existsSync(mainPath)) {
      errors.push(`Main process file not found: ${mainPath}`);
    } else {
      const source = fs.readFileSync(mainPath, 'utf-8');
      mainChannels = extractIpcMainChannels(source);
      info.push(`Found ${mainChannels.length} IPC channels in main process`);

      mainChannels.forEach((ch) => {
        if (!checkErrorHandlers(source, ch.name)) {
          warnings.push(`Channel "${ch.name}" in main process lacks try/catch error handling`);
        }
      });
    }
  }

  if (preloadPath) {
    if (!fs.existsSync(preloadPath)) {
      errors.push(`Preload script file not found: ${preloadPath}`);
    } else {
      const source = fs.readFileSync(preloadPath, 'utf-8');
      preloadChannels = extractPreloadExposedChannels(source);
      info.push(`Found ${preloadChannels.length} exposed channels in preload script`);
    }
  }

  if (contractPath) {
    if (!fs.existsSync(contractPath)) {
      errors.push(`Contract file not found: ${contractPath}`);
    } else {
      const markdown = fs.readFileSync(contractPath, 'utf-8');
      contractChannels = extractContractChannels(markdown);
      info.push(`Found ${contractChannels.length} channels in contract document`);
    }
  }

  if (mainPath && preloadPath) {
    const mainChannelNames = new Set(mainChannels.map((c) => c.name));
    const preloadChannelNames = new Set(preloadChannels.map((c) => c.channelName));

    mainChannelNames.forEach((name) => {
      if (!preloadChannelNames.has(name)) {
        warnings.push(`Channel "${name}" exists in main but is NOT exposed in preload`);
      }
    });

    preloadChannelNames.forEach((name) => {
      if (!mainChannelNames.has(name)) {
        errors.push(`Channel "${name}" exposed in preload but has NO handler in main process`);
      }
    });
  }

  if (mainPath && contractPath) {
    const mainChannelNames = new Set(mainChannels.map((c) => c.name));
    const contractChannelSet = new Set(contractChannels);

    mainChannelNames.forEach((name) => {
      if (!contractChannelSet.has(name)) {
        warnings.push(`Channel "${name}" in main process is NOT documented in contract`);
      }
    });

    contractChannelSet.forEach((name) => {
      if (!mainChannelNames.has(name)) {
        warnings.push(`Channel "${name}" documented in contract but NOT implemented in main`);
      }
    });
  }

  if (preloadPath && contractPath) {
    const preloadChannelNames = new Set(preloadChannels.map((c) => c.channelName));
    const contractChannelSet = new Set(contractChannels);

    preloadChannelNames.forEach((name) => {
      if (!contractChannelSet.has(name)) {
        warnings.push(`Channel "${name}" in preload is NOT documented in contract`);
      }
    });
  }

  console.log('\n=== IPC Contract Validation Report ===\n');

  if (verbose && info.length > 0) {
    console.log('📋 Info:');
    info.forEach((msg) => console.log(`   ${msg}`));
    console.log();
  }

  if (mainChannels.length > 0) {
    console.log('📡 Main Process Channels:');
    mainChannels.forEach((ch) => console.log(`   [${ch.type}] ${ch.name}`));
    console.log();
  }

  if (preloadChannels.length > 0) {
    console.log('🔗 Preload Exposed Channels:');
    preloadChannels.forEach((ch) => console.log(`   window.${ch.apiName}.${ch.methodName} → ${ch.channelName} (${ch.type})`));
    console.log();
  }

  if (contractChannels.length > 0) {
    console.log('📄 Contract Documented Channels:');
    contractChannels.forEach((name) => console.log(`   ${name}`));
    console.log();
  }

  if (warnings.length > 0) {
    console.log(`⚠️  Warnings (${warnings.length}):`);
    warnings.forEach((msg) => console.log(`   ${msg}`));
    console.log();
  }

  if (errors.length > 0) {
    console.log(`❌ Errors (${errors.length}):`);
    errors.forEach((msg) => console.log(`   ${msg}`));
    console.log();
  }

  const status = errors.length > 0 ? 'FAILED' : 'PASSED';
  const statusIcon = errors.length > 0 ? '❌' : '✅';
  console.log(`${statusIcon} Validation ${status}`);
  console.log(`   ${errors.length} errors, ${warnings.length} warnings\n`);

  process.exit(errors.length > 0 ? 1 : 0);
}

validate();
