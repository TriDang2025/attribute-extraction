CREATE TABLE "train" (
  "train id key" INTEGER,
  "total fee" NUMERIC(10, 2),
  "travel time" INTERVAL,
  "departure station" TEXT,
  "departure time" TIME,
  "payment location" TEXT,
  "reference number" INTEGER,
  "departure day" TEXT,
  "train id" INTEGER,
  "arrival time" TIME,
  "arrival station" TEXT,
  PRIMARY KEY ("train id key")
);

CREATE TABLE "hotel" (
  "reference number key" INTEGER,
  "generic accommodation type" TEXT,
  "phone number" INTEGER,
  "start date" TEXT,
  "reference number" INTEGER,
  "accommodation type" TEXT,
  "hotel name" TEXT,
  "number of options" INTEGER,
  "restaurant name" TEXT,
  "stars" INTEGER,
  "number of people" INTEGER,
  "price adjective" TEXT,
  "specific guesthouse" TEXT,
  "postcode" INTEGER,
  "number of nights" INTEGER,
  "location" TEXT,
  "address" TEXT,
  PRIMARY KEY ("reference number key")
);

CREATE TABLE "restaurant" (
  "reference number key" INTEGER,
  "price range question" TEXT,
  "restaurant name" TEXT,
  "postcode" INTEGER,
  "number of people" INTEGER,
  "price range confirmation" TEXT,
  "specific address" TEXT,
  "day of week" TEXT,
  "area" TEXT,
  "number of options" INTEGER,
  "restaurant type" TEXT,
  "restaurant reservation time" TIME,
  "food type" TEXT,
  "reference number" INTEGER,
  "restaurant reference number" INTEGER,
  "restaurant postcode" TEXT,
  "restaurant address" TEXT,
  PRIMARY KEY ("reference number key")
);
