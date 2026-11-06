CREATE TABLE "hotel" (
  "hotel_id" INTEGER,
  "name" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "stars" INTEGER,
  "price_range" TEXT,
  "free_wifi" BOOLEAN,
  "free_parking" BOOLEAN,
  "type" TEXT,
  PRIMARY KEY ("hotel_id")
);

CREATE TABLE "restaurant" (
  "restaurant_id" INTEGER,
  "name" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "price_range" TEXT,
  "cuisine" TEXT,
  PRIMARY KEY ("restaurant_id")
);

CREATE TABLE "attraction" (
  "attraction_id" INTEGER,
  "name" TEXT,
  "address" TEXT,
  "postcode" TEXT,
  "entrance_fee" NUMERIC(10, 2),
  "type" TEXT,
  PRIMARY KEY ("attraction_id")
);

CREATE TABLE "train" (
  "train_id" INTEGER,
  "train_number" TEXT,
  "departure_station" TEXT,
  "arrival_station" TEXT,
  "departure_time" TIME,
  "arrival_time" TIME,
  "travel_date" DATE,
  "price" NUMERIC(10, 2),
  PRIMARY KEY ("train_id")
);

CREATE TABLE "reservation" (
  "reservation_id" INTEGER,
  "hotel_id" INTEGER,
  "restaurant_id" INTEGER,
  "attraction_id" INTEGER,
  "train_id" INTEGER,
  "start_date" DATE,
  "end_date" DATE,
  "number_of_people" INTEGER,
  "reference_number" TEXT,
  PRIMARY KEY ("reservation_id"),
  FOREIGN KEY ("hotel_id") REFERENCES "hotel" ("hotel_id"),
  FOREIGN KEY ("restaurant_id") REFERENCES "restaurant" ("restaurant_id"),
  FOREIGN KEY ("attraction_id") REFERENCES "attraction" ("attraction_id"),
  FOREIGN KEY ("train_id") REFERENCES "train" ("train_id")
);

CREATE TABLE "taxi" (
  "taxi_id" INTEGER,
  "car_type" TEXT,
  "contact_number" TEXT,
  "pickup_location" TEXT,
  "dropoff_location" TEXT,
  "pickup_time" TIME,
  "dropoff_time" TIME,
  "reference_number" TEXT,
  PRIMARY KEY ("taxi_id")
);
