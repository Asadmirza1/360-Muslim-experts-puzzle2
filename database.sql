CREATE DATABASE IF NOT EXISTS heart_tracker;
USE heart_tracker;

-- Table for storing user information (signup/login)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    roll_number VARCHAR(20) NOT NULL UNIQUE,
    class_name VARCHAR(10) NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    password BLOB NOT NULL,  -- Store hashed password as bytes
    is_submitted BOOLEAN DEFAULT FALSE
);

-- Table for storing quiz responses
CREATE TABLE IF NOT EXISTS selections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    roll_number VARCHAR(20) NOT NULL,
    class_name VARCHAR(10) NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    disease VARCHAR(100) NOT NULL,
    symptom VARCHAR(100) NOT NULL,
    priority INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);