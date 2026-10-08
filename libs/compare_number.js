const fs = require('fs');

const enPath = 'lang/en.json';
const zhtwPath = 'lang/zh-tw.json';

const enData = JSON.parse(fs.readFileSync(enPath, 'utf8'));
const zhtwData = JSON.parse(fs.readFileSync(zhtwPath, 'utf8'));

function findNumberVars(obj, path = '', results = {}) {
    for (let key in obj) {
        const currentPath = path ? `${path}.${key}` : key;
        const val = obj[key];
        if (typeof val === 'string') {
            if (val.includes('{number}')) {
                results[currentPath] = val;
            }
        } else if (typeof val === 'object' && val !== null && !Array.isArray(val)) {
            findNumberVars(val, currentPath, results);
        }
    }
    return results;
}

const enNumbers = findNumberVars(enData);
const zhtwNumbers = findNumberVars(zhtwData);

const allKeys = new Set([...Object.keys(enNumbers), ...Object.keys(zhtwNumbers)]);

let onlyInEn = [];
let onlyInZhtw = [];
let inBoth = [];

for (const key of allKeys) {
    if (enNumbers[key] && !zhtwNumbers[key]) {
        onlyInEn.push(key);
    } else if (!enNumbers[key] && zhtwNumbers[key]) {
        onlyInZhtw.push(key);
    } else {
        inBoth.push(key);
    }
}

console.log("=== 僅在 EN 中包含 {number} 的項目 ===");
if (onlyInEn.length === 0) console.log("無");
onlyInEn.forEach(k => {
    let zhtwVal = '';
    // Helper to get zhtw value even if it doesn't contain {number}
    try {
        zhtwVal = k.split('.').reduce((o, i) => o[i], zhtwData);
    } catch (e) {}
    console.log(`- ${k}\n  EN:   ${enNumbers[k]}\n  TW:   ${zhtwVal}`);
});

console.log("\n=== 僅在 ZH-TW 中包含 {number} 的項目 ===");
if (onlyInZhtw.length === 0) console.log("無");
onlyInZhtw.forEach(k => {
    let enVal = '';
    try {
        enVal = k.split('.').reduce((o, i) => o[i], enData);
    } catch (e) {}
    console.log(`- ${k}\n  TW:   ${zhtwNumbers[k]}\n  EN:   ${enVal}`);
});

console.log(`\n=== 兩者皆包含 {number} 的項目數量: ${inBoth.length} ===`);
