CREATE TABLE "train" (
  "train id" INTEGER,
  "time str" INTEGER,
  "location capitalized" TEXT,
  "duration str" INTERVAL,
  "departure station" TEXT,
  "time" TIME,
  "price" NUMERIC(10, 2),
  PRIMARY KEY ("train id")
);

CREATE TABLE "hotel" (
  "entity" TEXT,
  "price range" TEXT,
  "day" TEXT,
  "hotel name" TEXT,
  "str" TEXT,
  "day of week" TEXT,
  "reference number" INTEGER,
  "price range str" TEXT,
  "num nights" INTEGER,
  "num people" INTEGER,
  "guest house name" TEXT,
  "date" TEXT,
  "num days" INTEGER,
  "location" TEXT,
  "location part" TEXT,
  "postcode" INTEGER,
  "party size" INTEGER,
  PRIMARY KEY ("reference number")
);

CREATE TABLE "restaurant" (
  "price range" TEXT,
  "num" INTEGER,
  "price range str" TEXT,
  "phone number" INTEGER,
  "date" TEXT,
  "location abbrev" TEXT,
  "str" TEXT,
  "cuisine" TEXT,
  "location area" TEXT,
  "location" TEXT,
  "venue name" TEXT,
  "time int" TIME,
  "day of week" TEXT,
  "price" TEXT,
  "reservation time" INTERVAL,
  "reference number" INTEGER,
  "location str" TEXT,
  "restaurant name" TEXT,
  "hotel id" INTEGER,
  PRIMARY KEY ("reference number"),
  FOREIGN KEY ("hotel id") REFERENCES "hotel" ("reference number")
);

CREATE TABLE "train_event" (
  "train_event id" INTEGER,
  "departure time" INTEGER,
  "time int" TIME,
  "day of week str" TEXT,
  PRIMARY KEY ("train_event id")
);

CREATE TABLE "restaurant_event" (
  "address key" INTEGER,
  "address" INTEGER,
  "time str" INTEGER,
  PRIMARY KEY ("address key")
);
