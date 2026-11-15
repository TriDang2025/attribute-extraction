CREATE TABLE "hotel" (
  "hotel" INTEGER,
  "str" TEXT,
  "hotel name" TEXT,
  "price" TEXT,
  "num people" INTEGER,
  "people" TEXT,
  "area" TEXT,
  "location" TEXT,
  "party size" TEXT,
  "num days" INTEGER,
  "price range" TEXT,
  "price range str" TEXT,
  "entity" TEXT,
  "num nights" INTEGER,
  "date" TEXT,
  "start date" TEXT,
  "guest house name" TEXT,
  PRIMARY KEY ("hotel")
);

CREATE TABLE "train" (
  "id" INTEGER,
  "train id" INTEGER,
  "reference number" INTEGER,
  "departure station" TEXT,
  "location str" TEXT,
  "day of week str" TEXT,
  "duration str" INTERVAL,
  "train id (train:14)" TIME,
  "total fee" TEXT,
  "departure location" TEXT,
  "travel time" TEXT,
  "price" NUMERIC(10, 2),
  "time" TIME,
  "time str" INTEGER,
  "departure time" INTEGER,
  "day of week" TEXT,
  "stansted airport" TEXT,
  PRIMARY KEY ("id")
);

CREATE TABLE "restaurant" (
  "restaurant name key" INTEGER,
  "price range" TEXT,
  "num ord" INTEGER,
  "price range str" TEXT,
  "num str" INTEGER,
  "date" TEXT,
  "location str" TEXT,
  "str" TEXT,
  "cuisine" TEXT,
  "num" INTEGER,
  "address" TEXT,
  "location area" TEXT,
  "venue name" TEXT,
  "time int" TIME,
  "phone number" INTEGER,
  "location" TEXT,
  "time str" TIME,
  "reservation time" INTERVAL,
  "reference number" INTEGER,
  "num card" INTEGER,
  "restaurant name" TEXT,
  PRIMARY KEY ("restaurant name key")
);

CREATE TABLE "attraction" (
  "postcode key" INTEGER,
  "address" TEXT,
  "attraction name" TEXT,
  "entrance fee" NUMERIC(10, 2),
  "location" TEXT,
  "cinema name" TEXT,
  "location str" TEXT,
  "attraction type" TEXT,
  "bed and breakfast" TEXT,
  "postcode" INTEGER,
  "favorite museum" TEXT,
  "location full" TEXT,
  "venue" TEXT,
  "street name" TEXT,
  PRIMARY KEY ("postcode key")
);

CREATE TABLE "attraction_2" (
  "attraction name key" INTEGER,
  "attraction name" TEXT,
  PRIMARY KEY ("attraction name key")
);
