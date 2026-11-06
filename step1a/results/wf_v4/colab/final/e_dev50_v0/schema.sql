CREATE TABLE "attraction" (
  "attraction_id" INTEGER,
  "name" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "entrance_fee" NUMERIC(10, 2),
  "type" TEXT,
  PRIMARY KEY ("attraction_id")
);

CREATE TABLE "restaurant" (
  "restaurant_id" INTEGER,
  "name" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "phone_number" TEXT,
  "price_range" TEXT,
  "cuisine" TEXT,
  PRIMARY KEY ("restaurant_id")
);

CREATE TABLE "hotel" (
  "hotel_id" INTEGER,
  "name" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "price_range" TEXT,
  "stars" INTEGER,
  "free_wifi" BOOLEAN,
  "free_parking" BOOLEAN,
  PRIMARY KEY ("hotel_id")
);

CREATE TABLE "train" (
  "train_id" INTEGER,
  "train_number" TEXT,
  "departure_station" TEXT,
  "arrival_station" TEXT,
  "departure_time" TIME,
  "arrival_time" TIME,
  "travel_time" INTERVAL,
  "price_per_ticket" NUMERIC(10, 2),
  "reference_number" TEXT,
  PRIMARY KEY ("train_id")
);

CREATE TABLE "reservation" (
  "reservation_id" INTEGER,
  "attraction_id" INTEGER,
  "restaurant_id" INTEGER,
  "hotel_id" INTEGER,
  "date" DATE,
  "time" TIME,
  "number_of_people" INTEGER,
  "reference_number" TEXT,
  PRIMARY KEY ("reservation_id"),
  FOREIGN KEY ("attraction_id") REFERENCES "attraction" ("attraction_id"),
  FOREIGN KEY ("restaurant_id") REFERENCES "restaurant" ("restaurant_id"),
  FOREIGN KEY ("hotel_id") REFERENCES "hotel" ("hotel_id")
);

CREATE TABLE "taxi" (
  "taxi_id" INTEGER,
  "pickup_location" TEXT,
  "dropoff_location" TEXT,
  "pickup_time" TIME,
  "car_type" TEXT,
  "contact_number" TEXT,
  "reference_number" TEXT,
  PRIMARY KEY ("taxi_id")
);
