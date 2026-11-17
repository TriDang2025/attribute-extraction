CREATE TABLE "train_schedule" (
  "reference number key" INTEGER,
  "date" TEXT,
  "destination" TEXT,
  "number of people" INTEGER,
  "price" NUMERIC(10, 2),
  "reference number" TEXT,
  "time int" TIME,
  "time str" TIME,
  "travel time" INTERVAL,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "accommodation_option" (
  "address key" INTEGER,
  "address" TEXT,
  "amenity" TEXT,
  "amenity str" TEXT,
  "area" TEXT,
  PRIMARY KEY ("address key")
);

CREATE TABLE "location" (
  "address key" INTEGER,
  "location" TEXT,
  "location name" TEXT,
  "location part" TEXT,
  "location str" TEXT,
  "address" INTEGER,
  "location (location:4)" TEXT,
  "museum" TEXT,
  "park" TEXT,
  "location (establishment:7)" TEXT,
  "location str (establishment:8)" TEXT,
  "postcode" INTEGER,
  PRIMARY KEY ("address key")
);

CREATE TABLE "establishment" (
  "reference number key" INTEGER,
  "college name" TEXT,
  "cuisine" TEXT,
  "date" TEXT,
  "day of week" TIME,
  "entity" TEXT,
  "entrance fee" NUMERIC(10, 2),
  "num people" INTEGER,
  "number of colleges" INTEGER,
  "party size" INTEGER,
  "price" TEXT,
  "reference number" INTEGER,
  "restaurant info" TEXT,
  "restaurant name" TEXT,
  "table booking" TEXT,
  "table reservation time" INTERVAL,
  "time" TIME,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "phone_number" (
  "phone number key" INTEGER,
  "phone number" INTEGER,
  "theatre" INTEGER,
  "phone number (establishment:12)" INTEGER,
  PRIMARY KEY ("phone number key")
);
