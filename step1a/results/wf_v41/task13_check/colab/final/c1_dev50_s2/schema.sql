CREATE TABLE "train_information" (
  "train_id" INTEGER,
  "train_duration" INTERVAL,
  "trainid" INTEGER,
  "departure" TEXT,
  "destination" TEXT,
  "leave_at" TIME,
  "price" NUMERIC(10, 2),
  "day" TEXT,
  "requested_people" INTEGER,
  "confirmed_reference" INTEGER,
  "arrive_by" TIME,
  PRIMARY KEY ("train_id")
);

CREATE TABLE "hotel_information" (
  "hotel_id" INTEGER,
  "area" TEXT,
  "name" TEXT,
  "requested_stay" INTEGER,
  "requested_day" TEXT,
  "type" TEXT,
  "address" TEXT,
  "price_range" TEXT,
  "confirmed_reference" INTEGER,
  "postcode" INTEGER,
  PRIMARY KEY ("hotel_id")
);

CREATE TABLE "restaurant_information" (
  "restaurant_id" INTEGER,
  "confirmed_reference" INTEGER,
  "address" TEXT,
  "requested_day" TEXT,
  "requested_people" INTEGER,
  "area" TEXT,
  "food" TEXT,
  "price_range" TEXT,
  "phone" INTEGER,
  "requested_time" TIME,
  "postcode" INTEGER,
  "name" TEXT,
  PRIMARY KEY ("restaurant_id")
);
