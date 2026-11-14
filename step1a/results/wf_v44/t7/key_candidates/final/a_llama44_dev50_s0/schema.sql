CREATE TABLE "train" (
  "departure station key" INTEGER,
  "currency" NUMERIC(10, 2),
  "departure station" TEXT,
  "departure time" INTEGER,
  "location capitalized" TEXT,
  "price" NUMERIC(10, 2),
  "time" TIME,
  "time int" TIME,
  "rest" TEXT,
  PRIMARY KEY ("departure station key")
);

CREATE TABLE "hotel" (
  "hotel name key" INTEGER,
  "date" TEXT,
  "day of week" TEXT,
  "hotel name" TEXT,
  "location" TEXT,
  "num days" INTEGER,
  "num nights" INTEGER,
  "num people" INTEGER,
  "rest" TEXT,
  PRIMARY KEY ("hotel name key")
);

CREATE TABLE "restaurant" (
  "restaurant name key" INTEGER,
  "cuisine" TEXT,
  "date" TEXT,
  "day of week" TEXT,
  "location" TEXT,
  "num" INTEGER,
  "phone number" INTEGER,
  "restaurant name" TEXT,
  "time int" TIME,
  "venue name" TEXT,
  "rest" TEXT,
  PRIMARY KEY ("restaurant name key")
);
