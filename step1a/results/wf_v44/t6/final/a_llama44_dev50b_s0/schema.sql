CREATE TABLE "train" (
  "date" TEXT,
  "destination" TEXT,
  "number of people" INTEGER,
  "price" NUMERIC(10, 2),
  "reference number" INTEGER,
  "train name" TEXT,
  "travel time" INTERVAL,
  "rest" TEXT,
  PRIMARY KEY ("number of people")
);

CREATE TABLE "hotel" (
  "checkin date" TEXT,
  "confirmation number" INTEGER,
  "day" TEXT,
  "day of week" TEXT,
  "hotel name" TEXT,
  "hotel rating" INTEGER,
  "location" TEXT,
  "type" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("confirmation number")
);

CREATE TABLE "restaurant" (
  "time int" TIME,
  "time str" TIME,
  "num" INTEGER,
  "num people" INTEGER,
  "college name" TEXT,
  "cuisine" TEXT,
  "date" TEXT,
  "location" TEXT,
  "location str" TEXT,
  "num options" INTEGER,
  "num people (restaurant:8)" INTEGER,
  "number of colleges" INTEGER,
  "party size" INTEGER,
  "phone number" INTEGER,
  "postcode" INTEGER,
  "price" TEXT,
  "price range" TEXT,
  "reference number" INTEGER,
  "restaurant name" TEXT,
  "str" TEXT,
  "table booking" TEXT,
  "table reservation time" TIME,
  "time" TIME,
  "rest" TEXT,
  PRIMARY KEY ("reference number")
);
