#!/usr/bin/env node

const { spawn } = require('child_process');
const { createWriteStream } = require('fs');

function startProcess(commandAndArguments, log) {
    var child = spawn(commandAndArguments[0], commandAndArguments.slice(1));
    child.stdout.pipe(process.stdout);
    child.stderr.pipe(process.stderr);
    process.stdin.pipe(child.stdin);
    const logStream = createWriteStream(log);

    function cleanWrite(prefix, data) {
        const lines = data.toString().split('\n');
        const filteredLines = lines.filter(line =>
            line.trim() !== '' &&
            !/Content-Length: \d+/.test(line) &&
            !/Content-Type: .+/.test(line)
        );
        if (filteredLines.length > 0) {
            const prefixedLines = filteredLines.map(line => prefix + line);
            logStream.write(prefixedLines.join('\n') + '\n');
        }
    }
    logStream.write('Starting process: ' + commandAndArguments.join(' ') + '\n');
    child.stdout.on('data', (data) => { cleanWrite("🔻", data); });
    child.stderr.on('data', (data) => { logStream.write("E " + data + "\n"); });
    process.stdin.on('data', (data) => { cleanWrite("🔼", data); });
}

let command;
let args;

if (!process.argv[1].includes('proxy.js')) {
    command = process.argv[1] + '-orig';
    args = process.argv.slice(2);
} else {
    command = process.argv[2];
    args = process.argv.slice(3);
}

if (!command) {
    console.error('No command provided.');
    process.exit(1);
}

startProcess([command, ...args], command + '.log');
