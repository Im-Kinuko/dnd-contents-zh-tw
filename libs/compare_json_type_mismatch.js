const fs = require('fs');

const enPath = 'lang/en.json';
const zhtwPath = 'lang/zh-tw.json';

const enData = JSON.parse(fs.readFileSync(enPath, 'utf8'));
const zhtwData = JSON.parse(fs.readFileSync(zhtwPath, 'utf8'));

let typeMismatches = [];

function checkTypeMismatches(enObj, zhtwObj, path = '') {
    for (let key in enObj) {
        if (key in zhtwObj) {
            const currentPath = path ? `${path}.${key}` : key;
            
            const isEnObj = typeof enObj[key] === 'object' && enObj[key] !== null && !Array.isArray(enObj[key]);
            const isZhtwObj = typeof zhtwObj[key] === 'object' && zhtwObj[key] !== null && !Array.isArray(zhtwObj[key]);

            if (isEnObj !== isZhtwObj) {
                typeMismatches.push(currentPath);
                // 用 en.json 的結構覆蓋，避免出現字串對上物件的錯誤
                zhtwObj[key] = JSON.parse(JSON.stringify(enObj[key]));
            } else if (isEnObj && isZhtwObj) {
                checkTypeMismatches(enObj[key], zhtwObj[key], currentPath);
            }
        }
    }
}

checkTypeMismatches(enData, zhtwData);

console.log("結構/類型不一致的鍵 (Type Mismatches):");
typeMismatches.forEach(k => console.log("- " + k));
console.log(`\n總共找到 ${typeMismatches.length} 個結構不一致的鍵。`);

fs.writeFileSync(zhtwPath, JSON.stringify(zhtwData, null, 2) + '\n', 'utf8');
console.log("\n已修正結構不一致的鍵，並使用英文預設值覆蓋以確保結構正確，最後已儲存 zh-tw.json。");
