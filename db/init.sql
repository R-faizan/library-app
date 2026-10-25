-- Runs automatically ONLY the first time the MySQL volume is empty.
CREATE TABLE IF NOT EXISTS books (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  author VARCHAR(120) NOT NULL,
  added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO books (title, author) VALUES
  ('The Phoenix Project', 'Gene Kim'),
  ('Docker Deep Dive', 'Nigel Poulton');
