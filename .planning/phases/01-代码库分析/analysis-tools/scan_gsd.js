#!/usr/bin/env node

const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const fs = require('fs');
const path = require('path');

const results = [];

function scanFile(filePath) {
  try {
    const code = fs.readFileSync(filePath, 'utf-8');
    const ast = parser.parse(code, {
      sourceType: 'unambiguous',
      plugins: ['jsx']
    });

    traverse(ast, {
      StringLiteral(path) {
        if (path.node.value.trim()) {
          results.push({
            file: filePath.replace(/\\/g, '/'),
            line: path.node.loc.start.line,
            col: path.node.loc.start.column,
            value: path.node.value,
            type: 'string'
          });
        }
      },
      TemplateLiteral(path) {
        path.node.quasis.forEach(quasi => {
          if (quasi.value.raw.trim()) {
            results.push({
              file: filePath.replace(/\\/g, '/'),
              line: quasi.loc.start.line,
              col: quasi.loc.start.column,
              value: quasi.value.raw,
              type: 'template'
            });
          }
        });
      }
    });
  } catch (err) {
    console.error(`Error parsing ${filePath}: ${err.message}`);
  }
}

function scanDirectory(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory() && entry.name !== 'node_modules') {
      scanDirectory(fullPath);
    } else if (entry.isFile() && (entry.name.endsWith('.js') || entry.name.endsWith('.cjs'))) {
      scanFile(fullPath);
    }
  }
}

const gsdDir = '.claude/get-shit-done';
scanDirectory(gsdDir);
console.log(JSON.stringify(results, null, 2));
