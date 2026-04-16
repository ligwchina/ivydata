const duckdb = require('duckdb');
const path = require('path');

const dbPath = path.join(__dirname, 'db/ivy.duckdb');

console.log('测试 DuckDB 并发访问...');
console.log('数据库路径:', dbPath);

// 测试 1: 只读连接
console.log('\n=== 测试 1: 只读连接 ===');
try {
  const db1 = new duckdb.Database(dbPath, duckdb.OPEN_READONLY);
  console.log('✅ 只读连接 1 成功');
  
  db1.all('SELECT COUNT(*) as count FROM base_data', (err, res) => {
    if (err) {
      console.error('查询失败:', err);
    } else {
      console.log('✅ 查询成功:', res);
    }
    
    db1.close();
    console.log('✅ 只读连接 1 已关闭');
  });
} catch (err) {
  console.error('❌ 只读连接失败:', err);
}

// 测试 2: 读写连接
setTimeout(() => {
  console.log('\n=== 测试 2: 读写连接 ===');
  try {
    const db2 = new duckdb.Database(dbPath);
    console.log('✅ 读写连接成功');
    
    db2.close();
    console.log('✅ 读写连接已关闭');
  } catch (err) {
    console.error('❌ 读写连接失败:', err);
  }
}, 1000);

// 测试 3: 同时打开两个只读连接
setTimeout(() => {
  console.log('\n=== 测试 3: 同时两个只读连接 ===');
  try {
    const db3a = new duckdb.Database(dbPath, duckdb.OPEN_READONLY);
    console.log('✅ 只读连接 3a 成功');
    
    const db3b = new duckdb.Database(dbPath, duckdb.OPEN_READONLY);
    console.log('✅ 只读连接 3b 成功');
    
    db3a.close();
    db3b.close();
    console.log('✅ 两个只读连接都已关闭');
  } catch (err) {
    console.error('❌ 多个只读连接失败:', err);
  }
}, 2000);

// 测试 4: 尝试启用 WAL 模式
setTimeout(() => {
  console.log('\n=== 测试 4: 检查 WAL 模式 ===');
  try {
    const db4 = new duckdb.Database(dbPath);
    
    db4.all('PRAGMA journal_mode', (err, res) => {
      if (err) {
        console.error('查询 journal_mode 失败:', err);
      } else {
        console.log('当前 journal_mode:', res);
      }
      
      // 尝试设置 WAL 模式
      db4.exec('PRAGMA journal_mode=WAL', (err) => {
        if (err) {
          console.error('设置 WAL 模式失败:', err);
        } else {
          console.log('✅ WAL 模式设置成功');
          
          db4.all('PRAGMA journal_mode', (err, res) => {
            if (!err) {
              console.log('新的 journal_mode:', res);
            }
            db4.close();
          });
        }
      });
    });
  } catch (err) {
    console.error('❌ WAL 模式测试失败:', err);
  }
}, 3000);
