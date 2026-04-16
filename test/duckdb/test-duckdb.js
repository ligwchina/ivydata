// 测试DuckDB连接的简单脚本
import duckdb from 'duckdb';

// 测试不同的路径格式
const paths = [
  'D:/dev/ai/ivydata/db/ivy.duckdb',
  'D:\\dev\\ai\\ivydata\\db\\ivy.duckdb',
  './db/ivy.duckdb'
];

// 测试只读模式
console.log('=== 测试只读模式 ===');
paths.forEach((path, index) => {
  console.log(`测试路径 ${index + 1}: ${path}`);
  try {
    console.log('尝试以只读模式连接...');
    const db = new duckdb.Database(path, { readOnly: true });
    console.log('连接成功!');
    // 尝试执行一个简单的查询
    db.all('SELECT 1 as test', (err, res) => {
      if (err) {
        console.error('查询失败:', err);
      } else {
        console.log('查询成功:', res);
      }
      db.close();
    });
  } catch (error) {
    console.error('连接失败:', error);
  }
  console.log('---');
});
