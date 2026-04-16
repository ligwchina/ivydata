export const config = {
  rabbitmq: {
    url: 'amqp://rabbitmq:rabbitmq@127.0.0.1:5672',
    prefetch: 1
  },
  python: {
    baseDataScript: 'D:\\dev\\ai\\ivydata\\data\\base_data_with_duckdb.py',
    klineDataScript: 'D:\\dev\\ai\\ivydata\\data\\day_k_data_with_duckdb.py',
    checkAndFillKlineDataScript: 'D:\\dev\\ai\\ivydata\\data\\check_and_fill_kline_data.py'
  }
}
