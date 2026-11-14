CREATE TABLE "train" (
  "travel time" INTERVAL,
  "time int" TIME,
  "number of people" INTEGER,
  "destination" TEXT,
  "price" NUMERIC(10, 2),
  "train name" TEXT,
  "date" TEXT,
  "time" TIME,
  "table reservation time" TIME,
  "rest" TEXT,
  PRIMARY KEY ("number of people")
);

CREATE TABLE "hotel" (
  "hotel id" INTEGER,
  "checkin date" TEXT,
  "num" INTEGER,
  "day" TEXT,
  "str" TEXT,
  "phone number" INTEGER,
  "num people" INTEGER,
  "hotel rating" INTEGER,
  "location" TEXT,
  "price range" TEXT,
  "hotel name" TEXT,
  "day of week" TEXT,
  "type" TEXT,
  "location part" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("hotel id")
);

CREATE TABLE "restaurant" (
  "restaurant name key" INTEGER,
  "reference number" INTEGER,
  "time str" TIME,
  "confirmation number" INTEGER,
  "price" TEXT,
  "number of colleges" INTEGER,
  "price range" TEXT,
  "party size" INTEGER,
  "date" TEXT,
  "location str" TEXT,
  "str" TEXT,
  "location" TEXT,
  "table booking" TEXT,
  "phone number" INTEGER,
  "reference number (restaurant:15)" INTEGER,
  "num people" INTEGER,
  "restaurant name" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("restaurant name key")
);
