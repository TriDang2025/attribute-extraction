CREATE TABLE "accommodation" (
  "reservation number key" INTEGER,
  "price range" TEXT,
  "amenities" TEXT,
  "hotel name" TEXT,
  "price" TEXT,
  "price range noun" TEXT,
  "start date" TEXT,
  "party size" TEXT,
  "reservation number" INTEGER,
  "num nights" INTEGER,
  "parking" TEXT,
  "guest house name" TEXT,
  "num days" INTEGER,
  "entity" TEXT,
  "num people" INTEGER,
  "internet" TEXT,
  "attribute" TEXT,
  "date" TEXT,
  "str" TEXT,
  "area" TEXT,
  "location" TEXT,
  PRIMARY KEY ("reservation number key")
);

CREATE TABLE "train_info" (
  "booking id key" INTEGER,
  "train id" TIME,
  "location abbr" TEXT,
  "currency" NUMERIC(10, 2),
  "departure time" INTEGER,
  "departure time (train_info:16)" TIME,
  "departure location" TEXT,
  "location type" TEXT,
  "location" TEXT,
  "seating_capacity" INTEGER,
  "travel time" TEXT,
  "total fee" TEXT,
  "departure day" TEXT,
  "booking id" INTEGER,
  PRIMARY KEY ("booking id key")
);

CREATE TABLE "location" (
  "reference number key" INTEGER,
  "attraction name" TEXT,
  "reference number" INTEGER,
  PRIMARY KEY ("reference number key")
);
