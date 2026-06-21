-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Novels Table
CREATE TABLE IF NOT EXISTS novels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    author VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    genre VARCHAR(100),
    published_year VARCHAR(10),
    image_url VARCHAR(500),
    is_borrowed BOOLEAN DEFAULT FALSE,
    borrowed_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borrowed_by) REFERENCES users(id)
);

-- Borrowed Novels Table
CREATE TABLE IF NOT EXISTS borrowed_novels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    novel_id INT NOT NULL,
    borrowed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    returned_at TIMESTAMP NULL,
    status VARCHAR(20) DEFAULT 'borrowed',
    due_date TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (novel_id) REFERENCES novels(id),
    UNIQUE KEY unique_borrow (user_id, novel_id, status)
);

-- Insert Default Novels
INSERT INTO novels (name, author, description, genre, published_year, image_url) VALUES
('Middlemarch', 'George Eliot', 
 'A masterpiece of Victorian literature exploring the lives of residents in a fictional English town. A deep examination of marriage, idealism, and social change in 19th-century England.',
 'Literary Fiction', '1871', 'middlemarch.jpg'),

('Beloved', 'Toni Morrison',
 'A powerful novel about the haunting legacy of slavery. Set after the American Civil War, it tells the story of Sethe, a former slave who is haunted by the ghost of her infant daughter.',
 'Historical Fiction', '1987', 'beloved.jpg'),

('Never Let Me Go', 'Kazuo Ishiguro',
 'A haunting dystopian novel about love, memory, and mortality. Set in a seemingly ordinary English boarding school where the students have a chillingly predetermined fate.',
 'Science Fiction', '2005', 'never-let-me-go.jpg'),

('The Secret History', 'Donna Tartt',
 'A dark academic thriller about a group of elite Classics students at a Vermont college who become entangled in a murder. A gripping exploration of guilt, obsession, and moral decay.',
 'Mystery', '1992', 'secret-history.jpg'),

('A Little Life', 'Hanya Yanagihara',
 'A profound and emotionally devastating novel about four friends navigating life in New York City. It explores themes of trauma, friendship, and the limits of love.',
 'Contemporary Fiction', '2015', 'little-life.jpg'),

('Crime and Punishment', 'Fyodor Dostoevsky',
 'A psychological masterpiece exploring guilt, redemption, and the nature of evil. Follows Raskolnikov, a destitute ex-student who plans and executes a murder for what he believes is a higher purpose.',
 'Classic Literature', '1866', 'crime-punishment.jpg')
ON DUPLICATE KEY UPDATE name=name;
