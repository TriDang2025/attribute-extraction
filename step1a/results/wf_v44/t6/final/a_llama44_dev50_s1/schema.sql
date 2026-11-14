CREATE TABLE "train" (
  "train id" INTEGER,
  "time str" INTEGER,
  "location capitalized" TEXT,
  "departure station" TEXT,
  "time" TIME,
  "price" NUMERIC(10, 2),
  "time int" TIME,
  "rest" TEXT,
  PRIMARY KEY ("train id")
);

CREATE TABLE "hotel" (
  "entity" TEXT,
  "hotel name" TEXT,
  "day of week" TEXT,
  "reference number" INTEGER,
  "location" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("reference number")
);

CREATE TABLE "restaurant" (
  "num" INTEGER,
  "phone number" INTEGER,
  "location" TEXT,
  "time int" TIME,
  "reference number" INTEGER,
  "restaurant name" TEXT,
  "hotel id" INTEGER,
  "rest" TEXT,
  PRIMARY KEY ("reference number"),
  FOREIGN KEY ("hotel id") REFERENCES "hotel" ("reference number")
);
