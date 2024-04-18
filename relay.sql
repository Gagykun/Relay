-- phpMyAdmin SQL Dump
-- version 5.2.1deb1ubuntu1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Apr 17, 2024 at 11:34 PM
-- Server version: 10.11.6-MariaDB-0ubuntu0.23.10.2
-- PHP Version: 8.2.10-2ubuntu1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `relay`
--

-- --------------------------------------------------------

--
-- Table structure for table `messages`
--

CREATE TABLE `messages` (
  `id` int(11) NOT NULL,
  `userID` varchar(255) NOT NULL,
  `recipientID` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `timestamp` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `messages`
--

INSERT INTO `messages` (`id`, `userID`, `recipientID`, `message`, `timestamp`) VALUES
(1, 'jXgI2ghbI6dftqrs', '0Vzf3Q544fymv44P', 'hey user!', '2024-04-04 03:51:56'),
(266, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'heyy', '2024-04-13 21:42:10'),
(267, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'hi guy!', '2024-04-13 21:42:13'),
(268, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', '^^', '2024-04-13 21:42:16'),
(269, 'jXgI2ghbI6dftqrs', '0Vzf3Q544fymv44P', 'hi man!', '2024-04-13 22:03:06'),
(270, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'sup!', '2024-04-13 22:03:12'),
(271, 'jXgI2ghbI6dftqrs', '0Vzf3Q544fymv44P', 'dude guess what happened today', '2024-04-13 22:03:19'),
(272, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'what happened gagy?', '2024-04-13 22:03:26'),
(273, 'jXgI2ghbI6dftqrs', '0Vzf3Q544fymv44P', 'i got better error handling in the API code :O', '2024-04-13 22:03:43'),
(274, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'NO WAY!', '2024-04-13 22:03:46'),
(275, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'dude that\'s going to help u a lot when it comes to debugging the code', '2024-04-13 22:03:59'),
(276, 'jXgI2ghbI6dftqrs', '0Vzf3Q544fymv44P', 'dude right! it\'s awesome!', '2024-04-13 22:05:31'),
(277, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'hey!', '2024-04-14 07:11:53'),
(278, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', '123', '2024-04-14 08:37:43'),
(279, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', ':p', '2024-04-17 05:19:33'),
(280, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', '123123123', '2024-04-17 05:27:09'),
(281, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'hey!!', '2024-04-17 22:51:02'),
(282, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'hiii', '2024-04-17 22:52:05'),
(283, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', ':p', '2024-04-17 22:54:25'),
(284, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', '1', '2024-04-17 22:58:51'),
(285, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', '123', '2024-04-17 23:00:42'),
(286, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'haha', '2024-04-17 23:00:47'),
(287, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'haayyyy', '2024-04-17 23:06:16'),
(288, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'aaaa', '2024-04-17 23:07:07'),
(289, '0Vzf3Q544fymv44P', 'jXgI2ghbI6dftqrs', 'oh yea!', '2024-04-17 23:07:11');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `userID` varchar(25) NOT NULL,
  `sessionID` varchar(32) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `salt` varchar(255) NOT NULL,
  `userName` varchar(45) NOT NULL,
  `email` varchar(255) NOT NULL,
  `userJoinDate` datetime NOT NULL,
  `lastLogin` timestamp(6) NULL DEFAULT NULL,
  `userStatus` varchar(45) NOT NULL,
  `profilePicture` varchar(255) DEFAULT NULL,
  `userBio` varchar(200) DEFAULT NULL,
  `friends` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci COMMENT='stores userdata';

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`userID`, `sessionID`, `password`, `salt`, `userName`, `email`, `userJoinDate`, `lastLogin`, `userStatus`, `profilePicture`, `userBio`, `friends`) VALUES
('0Vzf3Q544fymv44P', NULL, '03d0a5b9fadfb66bbc88edee3e83ab23a1b7e2786b60da7e127ea77d75c41b2d', 'aYJunwTss05fdoIr', 'user', 'user@user.com', '2024-03-12 19:02:21', '2024-04-17 23:07:00.000000', 'offline', NULL, NULL, 'jXgI2ghbI6dftqrs'),
('jXgI2ghbI6dftqrs', NULL, '955fdc32c9fc2f43a545da62cb658afebc9de2c3cb203eac7f0d0a9dc4ddc278', '68qi8LLT0wkVDGfW', 'gagy7', 'gagy7@live.com', '2024-03-14 16:10:20', '2024-04-13 22:02:55.000000', 'offline', NULL, NULL, '0Vzf3Q544fymv44P');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `messages`
--
ALTER TABLE `messages`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD UNIQUE KEY `userID` (`userID`),
  ADD UNIQUE KEY `userName` (`userName`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `profilePicture` (`profilePicture`),
  ADD UNIQUE KEY `sessionID` (`sessionID`),
  ADD KEY `idx_session_id` (`sessionID`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `messages`
--
ALTER TABLE `messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=290;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
