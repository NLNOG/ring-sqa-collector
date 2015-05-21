CREATE TABLE `sqa_collector` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `started` datetime NOT NULL,
  `ended` datetime DEFAULT NULL,
  `raised_by` varchar(45) NOT NULL DEFAULT 'unknown',
  `afi` enum('ipv4','ipv6') NOT NULL DEFAULT 'ipv4',
  `short` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1
