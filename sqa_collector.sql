-- MySQL Script generated by MySQL Workbench
-- Sun Jun 21 20:51:29 2015
-- Model: SQA Collector    Version: 1.0
-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema sqa_collector
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema sqa_collector
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `sqa_collector` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci ;
USE `sqa_collector` ;

-- -----------------------------------------------------
-- Table `sqa_collector`.`sqa_correlator`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sqa_collector`.`sqa_correlator` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `sqa_collector`.`sqa_correlator_objects`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sqa_collector`.`sqa_correlator_objects` (
  `id` INT(11) NOT NULL,
  `sqa_correlator_id` INT(11) NOT NULL,
  `object` VARCHAR(45) NOT NULL,
  `percentage` INT NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `sqa_correlator_id`
    FOREIGN KEY (`id`)
    REFERENCES `sqa_collector`.`sqa_correlator` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `sqa_collector`.`sqa_collector`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sqa_collector`.`sqa_collector` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `started` DATETIME NOT NULL,
  `ended` DATETIME NULL,
  `raised_by` VARCHAR(45) NOT NULL DEFAULT 'unknown',
  `afi` ENUM('ipv4','ipv6') NOT NULL DEFAULT 'ipv4',
  `short` VARCHAR(100) NULL,
  `long` TEXT(100) NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `sqa_collector`.`sqa_collector_correlator`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `sqa_collector`.`sqa_collector_correlator` (
  `id` INT(11) NOT NULL,
  `collector_id` INT(11) NOT NULL,
  `correlator_id` INT(11) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `collector_idx` (`collector_id` ASC),
  INDEX `correlator_idx` (`correlator_id` ASC),
  CONSTRAINT `sqa_collector_id`
    FOREIGN KEY (`collector_id`)
    REFERENCES `sqa_collector`.`sqa_collector` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `sqa_correlator_id`
    FOREIGN KEY (`correlator_id`)
    REFERENCES `sqa_collector`.`sqa_correlator_objects` (`id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

