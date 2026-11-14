CREATE TABLE "train" (
  "train id" INTEGER,
  "time int" TIME,
  "departure station" TEXT,
  "location capitalized" TEXT,
  "price" NUMERIC(10, 2),
  "time" TIME,
  "rest" TEXT,
  PRIMARY KEY ("train id")
);

CREATE TABLE "hotel" (
  "hotel id" INTEGER,
  "day of week" TEXT,
  "num days" INTEGER,
  "entity" TEXT,
  "hotel name" TEXT,
  "location" TEXT,
  "num people" INTEGER,
  "rest" TEXT,
  PRIMARY KEY ("hotel id")
);

CREATE TABLE "restaurant" (
  "venue name" TEXT,
  "cuisine" TEXT,
  "restaurant name" TEXT,
  "phone number" INTEGER,
  "time int" TIME,
  "num" INTEGER,
  "location" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("phone number")
);

CREATE TABLE "event" (
  "event id" INTEGER,
  "day of week str" TEXT,
  "day of week" TEXT,
  PRIMARY KEY ("event id")
);
