-- Drop database if it exists to start fresh (Use with caution!)
-- DROP DATABASE IF EXISTS CrimeRecords;

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS CrimeRecords;
USE CrimeRecords;

-- Drop tables in reverse order of dependency if they exist (for easy rerunning)
DROP TABLE IF EXISTS Reports;
DROP TABLE IF EXISTS Witnesses;
DROP TABLE IF EXISTS Crimes;
DROP TABLE IF EXISTS ReportedBy;
DROP TABLE IF EXISTS Evidence;
DROP TABLE IF EXISTS Officers;
DROP TABLE IF EXISTS Suspects;
DROP TABLE IF EXISTS Victims;


-- Create Tables (Order matters due to Foreign Keys)

CREATE TABLE Victims (
    VictimID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(255) NOT NULL,
    LastName VARCHAR(255) NOT NULL,
    DateOfBirth DATE,
    Address VARCHAR(255),
    PhoneNumber VARCHAR(20),
    Email VARCHAR(255)
);

CREATE TABLE Suspects (
    SuspectID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(255) NOT NULL,
    LastName VARCHAR(255) NOT NULL,
    DateOfBirth DATE,
    Address VARCHAR(255),
    PhoneNumber VARCHAR(20),
    CriminalRecord TEXT,
    KnownAliases VARCHAR(255)
);

CREATE TABLE Officers (
    OfficerID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(255) NOT NULL,
    LastName VARCHAR(255) NOT NULL,
    BadgeNumber VARCHAR(20) UNIQUE NOT NULL, -- Made BadgeNumber NOT NULL
    Rank1 VARCHAR(50), -- Kept original name 'Rank1'
    Department VARCHAR(255),
    ContactNumber VARCHAR(20),
    Email VARCHAR(255)
);

CREATE TABLE ReportedBy(
    ReportedByID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(255) NOT NULL,
    LastName VARCHAR(255) NOT NULL,
    DateOfBirth DATE,
    Address VARCHAR(255),
    PhoneNumber VARCHAR(20),
    Email VARCHAR(255)
);

CREATE TABLE Evidence (
    EvidenceID INT AUTO_INCREMENT PRIMARY KEY,
    EvidenceType VARCHAR(255),
    Description TEXT,
    DateCollected DATE,
    LocationCollected VARCHAR(255),
    CollectedByID INT, -- Officer who collected it
    -- Allow deleting officer without deleting evidence (sets CollectedByID to NULL)
    FOREIGN KEY (CollectedByID) REFERENCES Officers(OfficerID) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE Crimes (
    CrimeID INT AUTO_INCREMENT PRIMARY KEY,
    CrimeType VARCHAR(255) NOT NULL,
    Description TEXT,
    DateOfCrime DATE NOT NULL,
    TimeOfCrime TIME,
    Location VARCHAR(255),
    Status ENUM('Reported', 'Investigating', 'Closed', 'Pending') DEFAULT 'Reported',
    -- Foreign Keys (Allow NULLs as these might not be known initially)
    VictimID INT NULL,
    SuspectID INT NULL,
    OfficerID INT NULL,     -- Officer assigned to the case
    ReportedByID INT NULL,
    EvidenceID INT NULL,    -- A primary piece of evidence related (Optional: Consider a linking table if multiple evidence items per crime)

    -- Behavior on deleting linked records: SET NULL keeps the crime record
    FOREIGN KEY (VictimID) REFERENCES Victims(VictimID) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (SuspectID) REFERENCES Suspects(SuspectID) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (OfficerID) REFERENCES Officers(OfficerID) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (ReportedByID) REFERENCES ReportedBy(ReportedByID) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (EvidenceID) REFERENCES Evidence(EvidenceID) ON DELETE SET NULL ON UPDATE CASCADE -- Link to one primary evidence item
);

CREATE TABLE Witnesses (
    WitnessID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(255) NOT NULL,
    LastName VARCHAR(255) NOT NULL,
    DateOfBirth DATE,
    Address VARCHAR(255),
    PhoneNumber VARCHAR(20),
    Email VARCHAR(255),
    CrimeID INT NULL, -- Witness might be general or linked to a specific crime
    Statement TEXT,
    -- Behavior on deleting linked crime: SET NULL keeps witness, CASCADE deletes witness
    FOREIGN KEY (CrimeID) REFERENCES Crimes(CrimeID) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE Reports (
    ReportID INT AUTO_INCREMENT PRIMARY KEY,
    ReportDate DATE,
    ReportType VARCHAR(255),
    Description TEXT,
    CrimeID INT NULL,   -- Report might be general or about a specific crime
    OfficerID INT NULL, -- Officer filing the report

    -- Behavior on deleting linked records: CASCADE deletes report if crime deleted, SET NULL keeps report if officer deleted
    FOREIGN KEY (CrimeID) REFERENCES Crimes(CrimeID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (OfficerID) REFERENCES Officers(OfficerID) ON DELETE SET NULL ON UPDATE CASCADE
);

-- Add Indexes for performance on frequently queried columns (especially Foreign Keys)
ALTER TABLE Crimes ADD INDEX idx_crimedate (DateOfCrime);
ALTER TABLE Crimes ADD INDEX idx_fk_victim (VictimID);
ALTER TABLE Crimes ADD INDEX idx_fk_suspect (SuspectID);
ALTER TABLE Crimes ADD INDEX idx_fk_officer (OfficerID);
ALTER TABLE Crimes ADD INDEX idx_fk_reportedby (ReportedByID);
ALTER TABLE Crimes ADD INDEX idx_fk_evidence (EvidenceID);

ALTER TABLE Witnesses ADD INDEX idx_fk_crime (CrimeID);
ALTER TABLE Reports ADD INDEX idx_fk_crime_report (CrimeID);
ALTER TABLE Reports ADD INDEX idx_fk_officer_report (OfficerID);
ALTER TABLE Evidence ADD INDEX idx_fk_collectedby (CollectedByID);

SELECT 'Database setup complete.' AS Status;