IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='weather_logs' AND xtype='U')
BEGIN
    CREATE TABLE weather_logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        station_id VARCHAR(50) NOT NULL,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        pressure REAL NOT NULL,
        timestamp DATETIME NOT NULL DEFAULT GETDATE()
    );
END