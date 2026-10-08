const fs = require('fs');

const enPath = 'lang/en.json';
const zhtwPath = 'lang/zh-tw.json';

const enData = JSON.parse(fs.readFileSync(enPath, 'utf8'));
const zhtwData = JSON.parse(fs.readFileSync(zhtwPath, 'utf8'));

let extraKeys = [];

function checkAndRemoveExtras(enObj, zhtwObj, path = '') {
    let keysToRemove = [];
    for (let key in zhtwObj) {
        const currentPath = path ? `${path}.${key}` : key;
        if (!(key in enObj)) {
            extraKeys.push(currentPath);
            keysToRemove.push(key);
        } else {
            if (typeof zhtwObj[key] === 'object' && zhtwObj[key] !== null && !Array.isArray(zhtwObj[key])) {
                if (typeof enObj[key] === 'object' && enObj[key] !== null && !Array.isArray(enObj[key])) {
                    checkAndRemoveExtras(enObj[key], zhtwObj[key], currentPath);
                }
            }
        }
    }
    
    for (let key of keysToRemove) {
        delete zhtwObj[key];
    }
}

checkAndRemoveExtras(enData, zhtwData);

console.log("多出的鍵 (Extra Keys):");
extraKeys.forEach(k => console.log("- " + k));
console.log(`\n總共找到 ${extraKeys.length} 個多餘的鍵。`);

fs.writeFileSync(zhtwPath, JSON.stringify(zhtwData, null, 2) + '\n', 'utf8');
console.log("\n已刪除多餘的鍵並儲存 zh-tw.json。");
