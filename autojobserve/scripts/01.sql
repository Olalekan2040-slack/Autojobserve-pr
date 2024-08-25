DROP DATABASE IF EXISTS autojob;
CREATE DATABASE autojob;
USE autojob;

DROP TABLE IF EXISTS applied_jobs;
DROP TABLE IF EXISTS user_delete;
DROP TABLE IF EXISTS password;
DROP TABLE IF EXISTS location;
DROP TABLE IF EXISTS cvs;
DROP TABLE IF EXISTS jobtitle;
DROP TABLE IF EXISTS all_jobs;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS user_profile;
DROP TABLE IF EXISTS feedback_contacts;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    user_password VARCHAR(100) NOT NULL,
    job_title VARCHAR(100),
    user_location VARCHAR(255),
    cv VARCHAR(200)
) ENGINE=InnoDB;

CREATE TABLE all_jobs (
    job_id INT PRIMARY KEY AUTO_INCREMENT,
    job_title VARCHAR(255) NOT NULL,
    job_salary VARCHAR(255) NOT NULL,
    job_skill TEXT NOT NULL,
    job_location VARCHAR(255) NOT NULL,
    job_permalink VARCHAR(255),
    job_description VARCHAR(2000) DEFAULT NULL, 
    job_requirements VARCHAR(2000) DEFAULT NULL, 
    company_name VARCHAR(255) DEFAULT NULL,
    job_type VARCHAR(255) DEFAULT NULL,
    auto_apply BOOLEAN DEFAULT FALSE,
    is_saved_job BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(255) DEFAULT 'admin',
    modified_by VARCHAR(255) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE applied_jobs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    job_id INT NOT NULL,
    link_to_applied_jobs VARCHAR(255) NOT NULL,
    created_by VARCHAR(255) DEFAULT 'admin',
    modified_by VARCHAR(255) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (job_id) REFERENCES all_jobs(job_id)
) ENGINE=InnoDB;

CREATE TABLE saved_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    user_id INT NOT NULL,
    saved_job_title VARCHAR(255) NOT NULL,
    saved_job_salary VARCHAR(255) NOT NULL,
    saved_job_skill TEXT NOT NULL,
    saved_job_location VARCHAR(255) NOT NULL,
    saved_job_auto_apply BOOLEAN DEFAULT FALSE,
    -- saved_job_is_saved_job BOOLEAN DEFAULT FALSE,
    saved_job_permalink VARCHAR(255),
    saved_job_description VARCHAR(2000) DEFAULT NULL,
    saved_job_requirements VARCHAR(2000) DEFAULT NULL,
    saved_company_name VARCHAR(255),
    saved_job_type VARCHAR(255),
    created_by VARCHAR(255) DEFAULT 'admin',
    modified_by VARCHAR(255) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
    FOREIGN KEY (job_id) REFERENCES all_jobs(job_id), 
    FOREIGN KEY (user_id) REFERENCES users(id)    
) ENGINE=InnoDB;

CREATE TABLE password (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    user_password VARCHAR(255) NOT NULL,
    created_by VARCHAR(255) DEFAULT 'admin',
    modified_by VARCHAR(255) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

CREATE TABLE user_profile (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    bio VARCHAR(1000),
    website VARCHAR(255),
    phone_number VARCHAR(20),
    address VARCHAR(500),
    date_of_birth VARCHAR(10),
    gender VARCHAR(10),
    nationality VARCHAR(100),
    language VARCHAR(255),
    education VARCHAR(1000),
    work_experience VARCHAR(2000),
    job_description VARCHAR(1000),
    skills VARCHAR(2000),
    position VARCHAR(255),
    job_preference VARCHAR(255),
    social_media VARCHAR(255),
    experience_from_year INT,
    experience_to_year INT, 
    email_verified BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    restricted BOOLEAN,
    deactivated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    hidden BOOLEAN,
    deactivation_date DATETIME DEFAULT NULL,
    email_notifications BOOLEAN DEFAULT TRUE,
    mobile_messaging BOOLEAN DEFAULT TRUE,
    deleted BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(255) DEFAULT 'admin',
    modified_by VARCHAR(255) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;


CREATE TABLE location (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    user_location VARCHAR(255) DEFAULT NULL,
    created_by VARCHAR(255) DEFAULT 'admin',
    modified_by VARCHAR(255) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    user_profile_id INT,
    FOREIGN KEY (user_profile_id) REFERENCES user_profile(id)
) ENGINE=InnoDB;

CREATE TABLE cvs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    cv VARCHAR(200) DEFAULT NULL,
    created_by VARCHAR(255) DEFAULT 'admin',
    modified_by VARCHAR(255) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    user_profile_id INT,
    FOREIGN KEY (user_profile_id) REFERENCES user_profile(id)
) ENGINE=InnoDB;

CREATE TABLE jobtitle (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    job_title VARCHAR(255) DEFAULT NULL,
    created_by VARCHAR(255) DEFAULT 'admin',
    modified_by VARCHAR(255) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    user_profile_id INT,
    FOREIGN KEY (user_profile_id) REFERENCES user_profile(id)
) ENGINE=InnoDB;

CREATE TABLE feedback_contacts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message VARCHAR(1000) NOT NULL,
    created_by VARCHAR(255) DEFAULT 'admin',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- CREATE TABLE notifications (
--     id INT PRIMARY KEY AUTO_INCREMENT, 
--     user_id INT NOT NULL, 
--     message TEXT NOT NULL,
--     is_read BOOLEAN DEFAULT FALSE,
--     created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
--     FOREIGN KEY (user_id) REFERENCES users(id)
-- ) ENGINE=InnoDB;