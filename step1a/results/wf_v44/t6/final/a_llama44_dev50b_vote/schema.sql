CREATE TABLE "train" (
  "date" TEXT,
  "destination" TEXT,
  "number of people" INTEGER,
  "price" NUMERIC(10, 2),
  "reference number" INTEGER,
  "time int" TIME,
  "train name" TEXT,
  "travel time" INTERVAL,
  "rest" TEXT,
  PRIMARY KEY ("number of people")
);

CREATE TABLE "hotel" (
  "hotel name key" INTEGER,
  "checkin date" TEXT,
  "confirmation number" INTEGER,
  "day" TEXT,
  "day of week" TEXT,
  "hotel name" TEXT,
  "hotel rating" INTEGER,
  "location" TEXT,
  "num" INTEGER,
  "num people" INTEGER,
  "phone number" INTEGER,
  "type" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("hotel name key")
);

CREATE TABLE "restaurant" (
  "time str" TIME,
  "date" TEXT,
  "location" TEXT,
  "location str" TEXT,
  "num people" INTEGER,
  "number of colleges" INTEGER,
  "party size" INTEGER,
  "phone number" INTEGER,
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
