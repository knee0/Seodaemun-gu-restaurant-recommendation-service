import A_tokenize as step1
import B_score_aspects as step2
import C_add_name as step3
import D_show_visuals as step4

def run_pipeline():
    print("--- Start ABSA Pipeline ---")

    print("1/4: Tokenize reviews...")
    step1.main()

    print("2/4: Detecting sentiment...")
    step2.main()

    print("3/4: Adding restaurant names...")
    step3.main()

    print("4/4: Visualizing...")
    step4.main()
    
    print("--- All Done. ---")

if __name__ == "__main__":
    run_pipeline()
