from math import trunc

lst = []

for i in range(30):
    for _ in range(3):
        lst.append(i)

def find_by_length(df, nbr, down, hight, mid):
    result = []
    print(mid, ': ', df[mid], nbr)
    if df[mid] > nbr:
        print("go down")
        result = find_by_length(df, nbr, down, mid, ((mid - down) // 2) + down)

    elif df[mid] < nbr:
        print("go hight", mid, hight, ((hight - mid) // 2) + mid)
        result = find_by_length(df, nbr, mid, hight, ((hight - mid) // 2) + mid)

    
    mid_bis = mid - 1
    while df[mid_bis] == nbr:
        result.append(df[mid_bis])
        mid_bis = mid_bis - 1

    while df[mid] == nbr:
        result.append(df[mid])
        mid = mid + 1

    return result

def main_df_find_by_length(df, nbr):
    size = len(df)
    
    return find_by_length(df, nbr, 0, size, size // 2)

nbr = 13
index = main_df_find_by_length(lst, nbr)

print('\nobjectif : ', nbr)
index.append(5)
print('=>', index)
print('=>', list(reversed(index)))