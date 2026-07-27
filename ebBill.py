# Get user input for units consumed
units = float(input("Enter the number of units consumed: "))

if units < 0:
    print("Units consumed cannot be negative.")
else:
    # Calculate bill based on progressive slabs
    if units <= 100:
        total_bill = 0.0
    elif units <= 200:
        total_bill = (units - 100) * 2.15
    elif units <= 300:
        total_bill = (100 * 2.15) + (units - 200) * 4.15
    elif units <= 400:
        total_bill = (100 * 2.15) + (100 * 4.15) + (units - 300) * 5.15
    else:
        total_bill = (
            (100 * 2.15) + (100 * 4.15) + (100 * 5.15) + (units - 400) * 12.0
        )

    # Output the result
    print(f"Total Electricity Bill: ₹{total_bill:.2f}")