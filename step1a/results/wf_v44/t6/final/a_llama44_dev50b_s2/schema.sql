CREATE TABLE "train" (
  "departure day" TEXT,
  "number of people" INTEGER,
  "train name" TEXT,
  "time int" TIME,
  "reference number" INTEGER,
  "travel time" INTERVAL,
  "rest" TEXT,
  PRIMARY KEY ("number of people")
);

CREATE TABLE "hotel" (
  "time" TIME,
  "hotel name" TEXT,
  "hotel rating" INTEGER,
  "checkin date" TEXT,
  "num" INTEGER,
  "day" TEXT,
  "day of week" TEXT,
  "confirmation number" INTEGER,
  "phone number" INTEGER,
  "location" TEXT,
  "num people" INTEGER,
  "rest" TEXT,
  PRIMARY KEY ("confirmation number")
);

CREATE TABLE "restaurant" (
  "date" TEXT,
  "destination" TEXT,
  "time str" TIME,
  "time" TIME,
  "restaurant name" TEXT,
  "party size" INTEGER,
  "str" TEXT,
  "num people" INTEGER,
  "date (restaurant:3)" TEXT,
  "reference number" INTEGER,
  "location" TEXT,
  "table reservation time" TIME,
  "location str" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("reference number")
);
