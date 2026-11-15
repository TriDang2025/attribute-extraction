CREATE TABLE "train" (
  "departure day" TEXT,
  "number of people" INTEGER,
  "train name" TEXT,
  "time int" TIME,
  "reference number" INTEGER,
  "travel time" INTERVAL,
  PRIMARY KEY ("number of people")
);

CREATE TABLE "hotel" (
  "amenity str" TEXT,
  "amenity part" TEXT,
  "time" TIME,
  "hotel name" TEXT,
  "hotel rating" INTEGER,
  "amenity" TEXT,
  "checkin date" TEXT,
  "num" INTEGER,
  "day" TEXT,
  "price range" TEXT,
  "day of week" TEXT,
  "confirmation number" INTEGER,
  "type" TEXT,
  "address" TEXT,
  "rating" TEXT,
  "entity name" TEXT,
  "lodging type" TEXT,
  "phone number" INTEGER,
  "location" TEXT,
  "num people" INTEGER,
  "location name" TEXT,
  "str" TEXT,
  "location part" TEXT,
  PRIMARY KEY ("confirmation number")
);

CREATE TABLE "restaurant" (
  "reference number id" INTEGER,
  "entrance fee" NUMERIC(10, 2),
  "time" TIME,
  "cuisine" TEXT,
  "price range" TEXT,
  "restaurant info" TEXT,
  "restaurant name" TEXT,
  "party size" INTEGER,
  "str" TEXT,
  "price" TEXT,
  "num options" INTEGER,
  "num people" INTEGER,
  "date" TEXT,
  "reference number" INTEGER,
  "number of colleges" INTEGER,
  "postcode" INTEGER,
  "location" TEXT,
  "table reservation time" TIME,
  "phone number" INTEGER,
  "location str" TEXT,
  "college name" TEXT,
  PRIMARY KEY ("reference number id")
);

CREATE TABLE "train_booking" (
  "train_booking id" INTEGER,
  "date" TEXT,
  "destination" TEXT,
  "time str" TIME,
  PRIMARY KEY ("train_booking id")
);

CREATE TABLE "restaurant_booking" (
  "restaurant_booking id" INTEGER,
  "table booking" TEXT,
  PRIMARY KEY ("restaurant_booking id")
);
