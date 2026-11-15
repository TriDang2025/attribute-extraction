CREATE TABLE "train" (
  "train id" INTEGER,
  "time int" TIME,
  "departure station" TEXT,
  "location capitalized" TEXT,
  "time str" INTEGER,
  "price" NUMERIC(10, 2),
  "time" TIME,
  "departure time" INTEGER,
  "currency" NUMERIC(10, 2),
  PRIMARY KEY ("train id")
);

CREATE TABLE "hotel" (
  "day of week" TEXT,
  "day" TEXT,
  "num days" INTEGER,
  "num nights" INTEGER,
  "date" TEXT,
  "entity" TEXT,
  "price range" TEXT,
  "hotel name" TEXT,
  "location" TEXT,
  "guest house name" TEXT,
  "location part" TEXT,
  "reference number" INTEGER,
  "num people" INTEGER,
  "price range str" TEXT,
  "party size" INTEGER,
  "str" TEXT,
  "phone number" INTEGER,
  PRIMARY KEY ("reference number")
);

CREATE TABLE "restaurant" (
  "venue name" TEXT,
  "cuisine" TEXT,
  "price range str" TEXT,
  "reservation time" INTERVAL,
  "restaurant name" TEXT,
  "phone number" INTEGER,
  "str" TEXT,
  "price range" TEXT,
  "location area" TEXT,
  "location str" TEXT,
  "reference number" INTEGER,
  "time int" TIME,
  "num" INTEGER,
  "price" TEXT,
  "location" TEXT,
  "time str" INTEGER,
  "location abbrev" TEXT,
  "hotel id" INTEGER,
  PRIMARY KEY ("reference number"),
  FOREIGN KEY ("hotel id") REFERENCES "hotel" ("reference number")
);

CREATE TABLE "event" (
  "address id" INTEGER,
  "day of week str" TEXT,
  "travel time" TEXT,
  "postcode" INTEGER,
  "day of week" TEXT,
  "date" TEXT,
  "address" INTEGER,
  PRIMARY KEY ("address id")
);
