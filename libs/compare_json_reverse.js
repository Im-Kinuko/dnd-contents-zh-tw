const fs = require('fs');

const enPath = 'lang/en.json';
const zhtwPath = 'lang/zh-tw.json';

const enData = JSON.parse(fs.readFileSync(enPath, 'utf8'));
const zhtwData = JSON.parse(fs.readFileSync(zhtwPath, 'utf8'));

let missingKeys = [];

function addMissingKeys(enObj, zhtwObj, path = '') {
    for (let key in enObj) {
        const currentPath = path ? `${path}.${key}` : key;
        if (!(key in zhtwObj)) {
            missingKeys.push(currentPath);
            // Deep copy the missing value or structure from en.json
            zhtwObj[key] = JSON.parse(JSON.stringify(enObj[key]));
        } else {
            if (typeof enObj[key] === 'object' && enObj[key] !== null && !Array.isArray(enObj[key])) {
                if (typeof zhtwObj[key] === 'object' && zhtwObj[key] !== null && !Array.isArray(zhtwObj[key])) {
                    addMissingKeys(enObj[key], zhtwObj[key], currentPath);
                }
            }
        }
    }
}

addMissingKeys(enData, zhtwData);

console.log("缺少的鍵 (Missing Keys):");
missingKeys.forEach(k => console.log("- " + k));
console.log(`\n總共找到 ${missingKeys.length} 個缺少的鍵。`);

fs.writeFileSync(zhtwPath, JSON.stringify(zhtwData, null, 2) + '\n', 'utf8');
console.log("\n已將缺少的鍵補回並儲存 zh-tw.json。");
