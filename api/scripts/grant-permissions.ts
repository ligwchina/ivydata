import { Pool } from 'pg'

const adminPool = new Pool({
  host: '127.0.0.1',
  port: 5432,
  user: 'admin',
  password: 'kbaT2zFpEJS7wt58',
  database: 'ivydata'
})

async function grantPermissions() {
  const client = await adminPool.connect()
  try {
    await client.query('GRANT ALL ON SCHEMA public TO ivydata')
    await client.query('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ivydata')
    await client.query('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ivydata')
    await client.query('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ivydata')
    await client.query('ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ivydata')
    console.log('Permissions granted successfully')
  } finally {
    client.release()
    await adminPool.end()
  }
}

grantPermissions().catch(console.error)
