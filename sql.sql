-- Tabla eje del sistema
CREATE TABLE IF NOT EXISTS inventario_clientes (
    id INT(11) NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    estado DECIMAL(5,2) DEFAULT 0.00,
    director VARCHAR(255),
    resultado_json LONGTEXT,
    usuario_ejecutor VARCHAR(45),
    created_at INT(11),
    updated_at INT(11),
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


