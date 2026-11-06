CREATE TABLE "train_journey" (
  "train_journey_id" INTEGER,
  "train journey id" INTEGER,
  "departure location" TEXT,
  "departure time" TIME,
  "destination city" TEXT,
  "train id" INTEGER,
  "travel date" TEXT,
  "travel time" INTERVAL,
  PRIMARY KEY ("train journey id")
);

CREATE TABLE "hotel_booking" (
  "hotel_booking_id" INTEGER,
  "hotel booking id" INTEGER,
  "hotel location" TEXT,
  "hotel name" TEXT,
  "postcode" INTEGER,
  "price range" TEXT,
  "reference number" INTEGER,
  "star rating" INTEGER,
  "start date" TEXT,
  PRIMARY KEY ("hotel booking id")
);

CREATE TABLE "restaurant_reservation" (
  "restaurant_reservation_id" INTEGER,
  "restaurant reservation id" INTEGER,
  "postcode" INTEGER,
  "price range" TEXT,
  "reference number" INTEGER,
  "reservation date" TEXT,
  "reservation time" TIME,
  "restaurant address" TEXT,
  "restaurant area" TEXT,
  "restaurant food type" TEXT,
  "restaurant location" TEXT,
  "restaurant name" TEXT,
  "restaurant phone number" TEXT,
  PRIMARY KEY ("restaurant reservation id")
);
