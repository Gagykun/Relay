-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: db
-- Generation Time: Feb 18, 2024 at 04:17 AM
-- Server version: 11.2.3-MariaDB-1:11.2.3+maria~ubu2204
-- PHP Version: 8.2.15

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
  `lastLogin` varchar(45) DEFAULT NULL,
  `userStatus` varchar(45) NOT NULL,
  `profilePicture` varchar(255) DEFAULT NULL,
  `userBio` varchar(200) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_520_ci COMMENT='stores userdata';

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`userID`, `sessionID`, `password`, `salt`, `userName`, `email`, `userJoinDate`, `lastLogin`, `userStatus`, `profilePicture`, `userBio`) VALUES
('damvXds85K8zz3Oa', NULL, '1adf5f51747b9a2cbc8d5b8913f97eee3d3bbd0973d1747bb53745a272004724', '7i3vsbE1fLCYlgty', 'user', 'user@user', '2024-02-16 20:08:39', NULL, 'offline', NULL, NULL);

--
-- Indexes for dumped tables
--

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
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
