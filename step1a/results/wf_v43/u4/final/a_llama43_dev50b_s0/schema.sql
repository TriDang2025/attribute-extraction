CREATE TABLE "train_destination" (
  "train_destination id" INTEGER,
  "departure station" TEXT,
  "destination" TEXT,
  PRIMARY KEY ("train_destination id")
);

CREATE TABLE "train" (
  "number" INTEGER,
  "number of people" INTEGER,
  "pay location" TEXT,
  "time num" TIME,
  "time str" TEXT,
  "travel time" INTERVAL,
  PRIMARY KEY ("number")
);

CREATE TABLE "hotel" (
  "id" INTEGER,
  "2 star hotel" TEXT,
  "3 star guest houses" TEXT,
  "4 star guesthouse" TEXT,
  "4 star places" TEXT,
  "address" TEXT,
  "best guest house" TEXT,
  "date" INTEGER,
  "day of week" TEXT,
  "guesthouse" TEXT,
  "guesthouse name" TEXT,
  "hotel" TEXT,
  "hotel name" TEXT,
  "location" TEXT,
  "location area" TEXT,
  "location part" TEXT,
  "location str" TEXT,
  "lodging type" INTEGER,
  "num" INTEGER,
  "num days" INTEGER,
  "num guests" INTEGER,
  "num hotels" INTEGER,
  "num nights" INTEGER,
  "num people" INTEGER,
  "num people ordinal" INTEGER,
  "phone number" INTEGER,
  "place to stay" TEXT,
  "price" TEXT,
  "price range" TEXT,
  "reference number" TEXT,
  "time" TIME,
  PRIMARY KEY ("id")
);

CREATE TABLE "restaurant" (
  "restaurant name key" INTEGER,
  "address" TEXT,
  "cuisine" TEXT,
  "entrance fee" NUMERIC(10, 2),
  "famous college" TEXT,
  "location" TEXT,
  "location id" TEXT,
  "location str" TEXT,
  "num options" INTEGER,
  "number of people" TEXT,
  "phone number" INTEGER,
  "price range" TEXT,
  "price range str" TEXT,
  "reference number" TIME,
  "reservation duration" INTERVAL,
  "restaurant name" TEXT,
  "table" TEXT,
  "table size" INTEGER,
  "time" TIME,
  PRIMARY KEY ("restaurant name key")
);
