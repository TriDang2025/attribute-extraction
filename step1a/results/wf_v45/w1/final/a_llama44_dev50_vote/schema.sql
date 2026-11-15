CREATE TABLE "train" (
  "train id" INTEGER,
  "currency" NUMERIC(10, 2),
  "departure station" TEXT,
  "departure time" INTEGER,
  "duration str" INTERVAL,
  "location capitalized" TEXT,
  "price" NUMERIC(10, 2),
  "time" TIME,
  "time str" INTEGER,
  PRIMARY KEY ("train id")
);

CREATE TABLE "hotel" (
  "date" TEXT,
  "day" TEXT,
  "day of week" TEXT,
  "entity" TEXT,
  "guest house name" TEXT,
  "hotel name" TEXT,
  "location" TEXT,
  "location part" TEXT,
  "num days" INTEGER,
  "num nights" INTEGER,
  "num people" INTEGER,
  "party size" INTEGER,
  "price range" TEXT,
  "price range str" TEXT,
  "reference number" INTEGER,
  "str" TEXT,
  PRIMARY KEY ("reference number")
);

CREATE TABLE "restaurant" (
  "cuisine" TEXT,
  "date" TEXT,
  "day of week" TEXT,
  "location" TEXT,
  "location abbrev" TEXT,
  "location area" TEXT,
  "location str" TEXT,
  "num" INTEGER,
  "phone number" INTEGER,
  "price" TEXT,
  "price range" TEXT,
  "price range str" TEXT,
  "reference number" INTEGER,
  "reservation time" INTERVAL,
  "restaurant name" TEXT,
  "str" TEXT,
  "time int" TIME,
  "time str" INTEGER,
  "venue name" TEXT,
  PRIMARY KEY ("reference number")
);

CREATE TABLE "event" (
  "id" INTEGER,
  "day of week str" TEXT,
  "time int" TIME,
  "address" INTEGER,
  PRIMARY KEY ("id")
);
