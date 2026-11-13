CREATE TABLE "location" (
  "description" INTEGER,
  "payment location" TEXT,
  "arrival station" TEXT,
  "departure station" TEXT,
  "postcode" INTEGER,
  "address" TEXT,
  "location" TEXT,
  "postcode (restaurant:6)" INTEGER,
  "restaurant postcode" TEXT,
  "restaurant address" TEXT,
  "area" TEXT,
  PRIMARY KEY ("description")
);

CREATE TABLE "reservation" (
  "reference number key" INTEGER,
  "reference number" INTEGER,
  "number of tickets" INTEGER,
  "train id" INTEGER,
  "departure time" TIME,
  "arrival time" TIME,
  "total fee" NUMERIC(10, 2),
  "departure day" TEXT,
  "number of people" INTEGER,
  "number of options" INTEGER,
  "reference number (hotel:13)" INTEGER,
  "number of nights" INTEGER,
  "number of people (restaurant:5)" INTEGER,
  "day of week" TEXT,
  "price range question" TEXT,
  "reference number (restaurant:9)" INTEGER,
  "restaurant reservation time" TIME,
  "price range confirmation" TEXT,
  "restaurant reference number" INTEGER,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "amenity" (
  "id" INTEGER,
  "amenities" TEXT,
  "generic accommodation type" TEXT,
  "price adjective" TEXT,
  "hotel name" TEXT,
  "start date" TEXT,
  "restaurant name" TEXT,
  "specific guesthouse" TEXT,
  "accommodation type" TEXT,
  "stars" INTEGER,
  "food type" TEXT,
  "restaurant name (restaurant:12)" TEXT,
  "restaurant type" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "contact" (
  "phone number key" INTEGER,
  "phone number" INTEGER,
  "restaurant phone number" INTEGER,
  PRIMARY KEY ("phone number key")
);
