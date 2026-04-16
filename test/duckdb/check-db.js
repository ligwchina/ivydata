// 检查数据库中的数据
import duckdb from 'duckdb';

const dbPath = 'D:/dev/ai/ivydata/db/ivy.duckdb';

async function checkDatabase() {
  try {
    console.log('连接到数据库:', dbPath);
    const db = new duckdb.Database(dbPath);
    
    // 检查表是否存在
    db.all('SELECT name FROM sqlite_master WHERE type="table"', (err, tables) => {
      if (err) {
        console.error('检查表失败:', err);
        db.close();
        return;
      }
      
      console.log('数据库中的表:', tables);
      
      // 检查base_data表中的数据
      db.all('SELECT COUNT(*) as count FROM base_data', (err, result) => {
        if (err) {
          console.error('检查数据失败:', err);
          db.close();
          return;
        }
        
        console.log('base_data表中的数据行数:', result[0].count);
        
        // 查看前10条数据
        db.all('SELECT * FROM base_data LIMIT 10', (err, rows) => {
          if (err) {
            console.error('查看数据失败:', err);
            db.close();
            return;
          }
          
          console.log('前10条数据:', rows);
          db.close();
        });
      });
    });
  } catch (error) {
    console.error('连接数据库失败:', error);
  }
}

checkDatabase();
