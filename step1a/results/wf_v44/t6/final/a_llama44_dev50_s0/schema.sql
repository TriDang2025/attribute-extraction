CREATE TABLE "train" (
  "train id" INTEGER,
  "currency" NUMERIC(10, 2),
  "departure station" TEXT,
  "departure time" INTEGER,
  "location capitalized" TEXT,
  "price" NUMERIC(10, 2),
  "time" TIME,
  "time int" TIME,
  "rest" TEXT,
  PRIMARY KEY ("train id")
);

CREATE TABLE "hotel" (
  "hotel id" INTEGER,
  "date" TEXT,
  "day of week" TEXT,
  "hotel name" TEXT,
  "location" TEXT,
  "num days" INTEGER,
  "rest" TEXT,
  PRIMARY KEY ("hotel id")
);

CREATE TABLE "restaurant" (
  "cuisine" TEXT,
  "date" TEXT,
  "day of week" TEXT,
  "location" TEXT,
  "num" INTEGER,
  "phone number" INTEGER,
  "restaurant name" TEXT,
  "time int" TIME,
  "rest" TEXT,
  PRIMARY KEY ("phone number")
);
