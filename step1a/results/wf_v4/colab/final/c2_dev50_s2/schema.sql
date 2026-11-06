CREATE TABLE "train_information" (
  "train_id" INTEGER,
  "train_day" TEXT,
  "train_departure" TEXT,
  "train_leave_at" TIME,
  "train_duration" INTERVAL,
  "train_trainid" INTEGER,
  "train_price" NUMERIC(10, 2),
  "train_requested_people" INTEGER,
  "train_confirmed_reference" INTEGER,
  PRIMARY KEY ("train_id")
);

CREATE TABLE "hotel_information" (
  "hotel_id" INTEGER,
  "hotel_area" TEXT,
  "hotel_requested_day" TEXT,
  "hotel_price_range" TEXT,
  "hotel_stars" INTEGER,
  "hotel_name" TEXT,
  "hotel_confirmed_reference" INTEGER,
  "hotel_requested_stay" INTEGER,
  "hotel_requested_people" INTEGER,
  PRIMARY KEY ("hotel_id")
);

CREATE TABLE "restaurant_information" (
  "restaurant_id" INTEGER,
  "restaurant_area" TEXT,
  "restaurant_price_range" TEXT,
  "restaurant_food" TEXT,
  "restaurant_name" TEXT,
  "restaurant_confirmed_reference" INTEGER,
  "restaurant_requested_time" TIME,
  "restaurant_requested_day" TEXT,
  "restaurant_requested_people" INTEGER,
  PRIMARY KEY ("restaurant_id")
);
